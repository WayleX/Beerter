from fastapi import FastAPI, Request, HTTPException, status, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    "*", # React app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # List of allowed origins
    allow_credentials=True, # Allow cookies/auth headers
    allow_methods=["*"],    # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],    # Allow all headers (including Authorization)
)
class registerModel(BaseModel):
    nickname: str
    email: str
    password: str

class reviewModel(BaseModel):
    headline: str
    review: str
    rating: int
    product_id: str

class loginModel(BaseModel):
    email: str
    password: str


class UserDatabase:
    def __init__(self):
        self.users = {}
        self.hasher = CryptContext(schemes=["sha256_crypt"])

    def add_user(self, user: registerModel):
        if user.email in self.users:
            raise HTTPException(status_code=400, detail="User already exists")
        
        hashed_password = self.hasher.hash(user.password)

        self.users[user.email] = {
            "nickname": user.nickname,
            "email": user.email,
            "password": hashed_password
        }
    
    def verify_user(self, email: str, password: str):
        user = self.users.get(email)
 
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        if not self.hasher.verify(password, user["password"]):
            raise HTTPException(status_code=400, detail="Incorrect password")
        
        return True
    

class TokenGenerator:
    def __init__(self, users_db):
        self.users_db = users_db
        self.SECRET_KEY = "your_super_secret"
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    def create_token(self, user: loginModel):
        to_encode = user.dict()
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token
    
    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            user_email = payload.get("email")
            if user_email not in self.users_db.users:
                raise HTTPException(status_code=401, detail="Invalid user in token")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")



SECRET_KEY = "your_super_secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


security = HTTPBearer()

users = UserDatabase()

token_generator = TokenGenerator(users_db=users)


@app.post("/register")
def register(data: registerModel):
    username = data.nickname
    password = data.password
    email = data.email
    print("LOG: Registering user:", username)
    if not username or not password or not email:
        raise HTTPException(status_code=400, detail="Missing username or password or email")
    users.add_user(data)

    return {"msg": "User registered successfully"}

@app.post("/login")
def login(data: loginModel):
    print("LOG: Logging in incoming")
    email = data.email
    password = data.password
    print("LOG: Logging in user:", email)
    if not users.verify_user(email, password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = token_generator.create_token(data)
    return {"access_token": token}


@app.get("/verify")
def verify(
    authorization: Annotated[str | None, Header()] = None
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    payload = token_generator.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_email = payload.get("email")
    if user_email not in users.users:
        raise HTTPException(status_code=401, detail="Invalid user in token")
    return {
        "user_email": user_email,
        "msg": "Token is valid"
    }

reviews = []

@app.post("/post_review")
def post_review(data:reviewModel, authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    payload = token_generator.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_email = payload.get("email")
    reviews.append({
        "review": data.review,
        "headline": data.headline,
        "rating": data.rating,
        "product_id": data.product_id,
        "user_email": user_email
    })

@app.get("/get_reviews")
def get_recent_reviews():
    return reviews[-5:]

@app.get("/get_all_reviews")
def get_all_reviews():
    return reviews

class GetReviewsByProductId(BaseModel):
    product_id: str

@app.get("/get_reviews_by_product/{product_id}")
def get_reviews_by_product(product_id: str, authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    payload = token_generator.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    product_reviews = [review for review in reviews if review["product_id"] == product_id]
    return product_reviews

@app.get("/get_all_beers")
def get_all_beers():
    return [
        {
            "id": 1,
            "name": "Beer 1",
            "description": "Description of Beer 1",
            "image_url": "https://example.com/beer1.jpg"
        },
        {
            "id": 2,
            "name": "Beer 2",
            "description": "Description of Beer 2",
            "image_url": "https://example.com/beer2.jpg"
        }
    ]


@app.get("/post_like")
def post_like(product_id: str, authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    payload = token_generator.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_email = payload.get("email")

    return {"msg": f"Liked product {product_id} by user {user_email}"}

