from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import os
from typing import Annotated
from typing import Optional
from database import get_db, create_tables, User, Like, BlacklistedToken
from models import UserRegister, UserLogin, UserInDB
import consul
import random
import pika
import json

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

c = consul.Consul(host="consul", port=8500)


port = int(os.getenv("USER_SERVICE_PORT", "8001"))
service_name = "beer_review_user_service"
c.agent.service.register(
    name=service_name,
    service_id=str(random.randint(1, 100000)),
    port=port,

    check=consul.Check.http(
        url = f"http://beer_review_user_service_{port}:{port}/",
        interval="10s"
        
    )
)
# Security
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# RabbitMQ connection and channel
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')
parameters = pika.URLParameters(RABBITMQ_URL)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue='likes', durable=True)

# Helper to publish events with a fresh connection
def publish_event(event: dict):
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.queue_declare(queue='likes', durable=True)
    ch.basic_publish(
        exchange='', routing_key='likes',
        body=json.dumps(event),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()

# Create DB tables
@app.on_event("startup")
def startup_event():
    create_tables()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if email is None:
            return None
        # reject blacklisted tokens
        if db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first():
            return None
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            return None
        return {"user_email": email, "user_id": user.id, "nickname": user.nickname}
    except jwt.PyJWTError:
        return None

@app.get("/")
def read_root():
    return {"message": "User API"}

@app.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, nickname=user.nickname, password=hashed_password)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"msg": "User registered successfully"}

@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token({"email": user.email})
    return {"access_token": access_token}

@app.get("/verify")
def verify_user(authorization: Annotated[Optional[str], Header()] = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token, db)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "user_email": payload["user_email"],
        "nickname": payload["nickname"],
        "msg": "Token is valid"
    }

@app.post("/logout")
def logout_user(authorization: Annotated[Optional[str], Header()] = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split()[1]
    # ensure token is valid and not already blacklisted
    payload = verify_token(token, db)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    # add to blacklist
    black = BlacklistedToken(token=token)
    db.add(black)
    db.commit()
    return {"msg": "Logged out successfully"}

@app.post("/like")
async def like_post(post_id: str, authorization: Annotated[Optional[str], Header()] = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split()[1]
    user_info = verify_token(token, db)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = user_info["user_id"]
    # Publish a 'like' event to RabbitMQ
    event = {"type": "like", "user_id": user_id, "post_id": post_id, "timestamp": datetime.utcnow().isoformat()}
    publish_event(event)
    # also save like directly for immediate effect
    exists = db.query(Like).filter(Like.user_id == user_id, Like.post_id == post_id).first()
    if not exists:
        db.add(Like(user_id=user_id, post_id=post_id))
        db.commit()
    return {"msg": "Like event published", "post_id": post_id}

@app.delete("/like")
async def unlike_post(post_id: str, authorization: Annotated[Optional[str], Header()] = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split()[1]
    user_info = verify_token(token, db)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = user_info["user_id"]
    # Publish an 'unlike' event to RabbitMQ
    event = {"type": "unlike", "user_id": user_id, "post_id": post_id, "timestamp": datetime.utcnow().isoformat()}
    publish_event(event)
    # also remove like directly for immediate effect
    db.query(Like).filter(Like.user_id == user_id, Like.post_id == post_id).delete()
    db.commit()
    return {"msg": "Unlike event published", "post_id": post_id}

@app.get("/likes")
async def get_likes(authorization: Annotated[Optional[str], Header()] = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split()[1]
    user_info = verify_token(token, db)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = user_info["user_id"]
    likes = db.query(Like).filter(Like.user_id == user_id).all()
    return [like.post_id for like in likes]

# Run with: uvicorn main:app --host 0.0.0.0 --port 8001