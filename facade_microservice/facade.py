from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from typing import Annotated, Optional
from fastapi.middleware.cors import CORSMiddleware
import consul
import random
import csv
import os
import pika, json
from datetime import datetime

app = FastAPI()

# Load beer data from CSV
_BEER_CSV = os.path.join(os.path.dirname(__file__), 'beer.csv')
_beer_records = []
try:
    with open(_BEER_CSV, newline='', encoding='utf-8') as _f:
        _reader = csv.DictReader(_f)
        for _row in _reader:
            _beer_records.append(_row)
except FileNotFoundError:
    print(f"beer.csv not found at {_BEER_CSV}")

# CORS setup
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

c = consul.Consul(host="consul", port=8500)

port = 8009
service_name = "facade-service"
c.agent.service.register(
    name=service_name,
    service_id=service_name,
    port=port,
    check=consul.Check.http(
        url = f"http://beer_review_facade_service:{port}/",
        interval="10s"
    )
)

# RabbitMQ setup
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')

def publish_event(event: dict):
    # create fresh connection and channel per event
    params = pika.URLParameters(RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue='likes', durable=True)
    ch.basic_publish(
        exchange='', routing_key='likes',
        body=json.dumps(event),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()

def find_service(service_name):
    c = consul.Consul(host="consul", port=8500)
    try:
        _, nodes = c.health.service(service_name)
        service_ports = [node['Service']['Port'] for node in nodes]
    except Exception:
        service_ports = []
    if not service_ports:
        svcs = c.agent.services()
        service_ports = [svc['Port'] for svc in svcs.values() if svc['Service'] == service_name]
    return service_ports

def find_service_endpoint(service_name):
    """Discover service instances with address and port via Consul health or agent APIs"""
    _, nodes = c.health.service(service_name, passing=True)
    endpoints = [(n['Service']['Address'], n['Service']['Port']) for n in nodes]
    if not endpoints:
        svcs = c.agent.services()
        endpoints = [(svc['Address'], svc['Port']) for svc in svcs.values() if svc['Service'] == service_name]
    if not endpoints:
        raise HTTPException(status_code=503, detail=f"{service_name} not available")
    return endpoints

def extract_error_detail(e, default_msg: str):
    """Safely extract JSON 'detail' from HTTPX response or fall back to text/default."""
    resp = getattr(e, 'response', None)
    if resp is not None:
        try:
            return resp.json().get('detail', default_msg)
        except ValueError:
            text = resp.text
            return text if text else default_msg
    return str(e)

# Models
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

class updateReviewModel(BaseModel):
    headline: Optional[str] = None
    review: Optional[str] = None
    rating: Optional[int] = None
    product_id: Optional[str] = None

async def verify_token_facade(token: str):
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('beer_review_user_service')
            port  = random.choice(ports)
            USER_SERVICE_URL = f"http://beer_review_user_service_{port}:{port}"
            response = await client.get(
                f"{USER_SERVICE_URL}/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Authentication service error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

# Auth helper function
async def get_user_from_token(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    return await verify_token_facade(token)


@app.get("/")
async def read_root():
    return {"message": "Facade API"}

# API Routes
@app.post("/register")
async def register(data: registerModel):
    print("LOG: Registering user:", data.nickname)
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('beer_review_user_service')
            port  = random.choice(ports)
            USER_SERVICE_URL = f"http://beer_review_user_service_{port}:{port}"
            print("LOG: User service URL:", USER_SERVICE_URL)
            response = await client.post(f"{USER_SERVICE_URL}/register", json=data.dict())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Registration error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.post("/login")
async def login(data: loginModel):
    print("LOG: Logging in user:", data.email)
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('beer_review_user_service')
            port  = random.choice(ports)
            USER_SERVICE_URL = f"http://beer_review_user_service_{port}:{port}"
            
            response = await client.post(f"{USER_SERVICE_URL}/login", json=data.dict())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Login error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/verify")
async def verify(authorization: Annotated[str | None, Header()] = None):
    return await get_user_from_token(authorization)

@app.post("/logout")
async def logout(authorization: Annotated[str | None, Header()] = None):
    # ensure token header is present and valid
    await get_user_from_token(authorization)
    raw_token = authorization
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('beer_review_user_service')
            port = random.choice(ports)
            USER_SERVICE_URL = f"http://beer_review_user_service_{port}:{port}"
            response = await client.post(
                f"{USER_SERVICE_URL}/logout",
                headers={"Authorization": raw_token}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Logout error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.post("/post_review")
async def post_review(data: reviewModel, authorization: Annotated[str | None, Header()] = None):
    # authenticate user and retrieve details
    user_data = await get_user_from_token(authorization)
    # forward to reviews microservice
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('reviews-service')
            port = random.choice(ports)
            REVIEW_SERVICE_URL = f"http://reviews_backend_{port}:{port}"
            payload = data.dict()
            # attach user identity
            payload["user_email"] = user_data["user_email"]
            payload["user_nickname"] = user_data.get("nickname")
            response = await client.post(f"{REVIEW_SERVICE_URL}/reviews/", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Review service error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/get_reviews")
async def get_recent_reviews(authorization: Annotated[str | None, Header()] = None):
    async with httpx.AsyncClient() as client:
        # ensure token is valid
        await get_user_from_token(authorization)
        try:
            ports = find_service('reviews-service')
            port = random.choice(ports)
            REVIEW_SERVICE_URL = f"http://reviews_backend_{port}:{port}"
            response = await client.get(f"{REVIEW_SERVICE_URL}/reviews/", headers={"Authorization": authorization})
            response.raise_for_status()
            data = response.json()
            return data[-5:]
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Review fetch error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/get_all_reviews")
async def get_all_reviews(authorization: Annotated[str | None, Header()] = None):
    async with httpx.AsyncClient() as client:
        # ensure token is valid
        await get_user_from_token(authorization)
        try:
            ports = find_service('reviews-service')
            port = random.choice(ports)
            REVIEW_SERVICE_URL = f"http://reviews_backend_{port}:{port}"
            response = await client.get(f"{REVIEW_SERVICE_URL}/reviews/", headers={"Authorization": authorization})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Review fetch error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/get_reviews_by_product/{product_id}")
async def get_reviews_by_product(product_id: str, authorization: Annotated[str | None, Header()] = None):
    # authenticate user
    await get_user_from_token(authorization)
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('reviews-service')
            port = random.choice(ports)
            REVIEW_SERVICE_URL = f"http://reviews_backend_{port}:{port}"
            response = await client.get(f"{REVIEW_SERVICE_URL}/reviews/", headers={"Authorization": authorization})
            response.raise_for_status()
            data = response.json()
            return [r for r in data if r.get("product_id") == product_id]
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Review fetch error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/get_reviews_by_keyword/{keyword}")
async def get_reviews_by_keyword(keyword: str, authorization: Annotated[str | None, Header()] = None):
    # authenticate user
    await get_user_from_token(authorization)
    # forward keyword search to reviews microservice
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('reviews-service')
            port = random.choice(ports)
            REVIEW_SERVICE_URL = f"http://reviews_backend_{port}:{port}"
            response = await client.get(f"{REVIEW_SERVICE_URL}/reviews/keyword/{keyword}", headers={"Authorization": authorization})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Review fetch error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/get_reviews_by_user")
async def get_reviews_by_user(authorization: Annotated[str | None, Header()] = None):
    # Authenticate and get user info
    user_info = await get_user_from_token(authorization)
    user_email = user_info.get("user_email")
    if not user_email:
        raise HTTPException(status_code=400, detail="User email not found in token")
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('reviews-service')
            port = random.choice(ports)
            REVIEW_SERVICE_URL = f"http://reviews_backend_{port}:{port}"
            response = await client.get(f"{REVIEW_SERVICE_URL}/reviews/", headers={"Authorization": authorization})
            response.raise_for_status()
            all_reviews = response.json()
            user_reviews = [r for r in all_reviews if r.get("user_email") == user_email]
            return user_reviews
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Review fetch error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/get_review/{review_id}")
async def get_review(review_id: str, authorization: Annotated[str | None, Header()] = None):
    # authenticate user
    await get_user_from_token(authorization)
    raw_token = authorization
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('reviews-service')
            port = random.choice(ports)
            REVIEW_SERVICE_URL = f"http://reviews_backend_{port}:{port}"
            response = await client.get(
                f"{REVIEW_SERVICE_URL}/reviews/{review_id}",
                headers={"Authorization": raw_token}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if getattr(e, 'response', None) else 500
            detail = extract_error_detail(e, "Review fetch error")
            raise HTTPException(status_code=status_code, detail=detail)

@app.put("/edit_review/{review_id}")
async def edit_review(
    review_id: str,
    update_data: updateReviewModel,
    authorization: Annotated[str | None, Header()] = None
):
    # authenticate user
    await get_user_from_token(authorization)
    raw_token = authorization
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('reviews-service')
            port = random.choice(ports)
            REVIEW_SERVICE_URL = f"http://reviews_backend_{port}:{port}"
            # send only set fields
            payload = update_data.dict(exclude_unset=True)
            response = await client.put(
                f"{REVIEW_SERVICE_URL}/reviews/{review_id}",
                json=payload,
                headers={"Authorization":raw_token}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if getattr(e, 'response', None) else 500
            detail = extract_error_detail(e, "Review update error")
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/get_all_beers")
def get_all_beers():
    # Return records as read from CSV
    return _beer_records

@app.get("/beers")
def list_beer_names():
    """Return only the list of beer names from the CSV"""
    return [r.get('Name') for r in _beer_records]

@app.post("/post_like/{review_id}")
async def post_like(review_id: str, authorization: Annotated[str | None, Header()] = None):
    user = await get_user_from_token(authorization)
    uid = user.get('user_id') or user.get('id')
    if uid is None:
        raise HTTPException(status_code=500, detail="user_id missing from verify response")
    event = {"type": "like", "user_id": uid, "post_id": review_id, "timestamp": datetime.utcnow().isoformat()}
    publish_event(event)
    return {"msg": "Like event published", "post_id": review_id}

@app.delete("/post_like/{review_id}")
async def delete_like(review_id: str, authorization: Annotated[str | None, Header()] = None):
    user = await get_user_from_token(authorization)
    uid = user.get('user_id') or user.get('id')
    if uid is None:
        raise HTTPException(status_code=500, detail="user_id missing from verify response")
    event = {"type": "unlike", "user_id": uid, "post_id": review_id, "timestamp": datetime.utcnow().isoformat()}
    publish_event(event)
    return {"msg": "Unlike event published", "post_id": review_id}

@app.get("/get_likes")
async def get_likes(authorization: Annotated[str | None, Header()] = None):
    # authenticate and retrieve liked posts
    raw_token = authorization
    await get_user_from_token(authorization)
    async with httpx.AsyncClient() as client:
        try:
            ports = find_service('beer_review_user_service')
            port = random.choice(ports)
            USER_SERVICE_URL = f"http://beer_review_user_service_{port}:{port}"
            response = await client.get(
                f"{USER_SERVICE_URL}/likes",
                headers={"Authorization": raw_token}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, "response") else 500
            detail = e.response.json().get("detail", "Fetch likes error") if hasattr(e, "response") else str(e)
            raise HTTPException(status_code=status_code, detail=detail)

@app.post("/refresh_feed")
async def refresh_feed(authorization: Annotated[str | None, Header()] = None):
    # authenticate user
    await get_user_from_token(authorization)
    raw_token = authorization
    async with httpx.AsyncClient() as client:
        try:
            # use Consul-discovered endpoints for feed-service
            endpoints = find_service_endpoint('feed-service')
            host, port = random.choice(endpoints)
            FEED_URL = f"http://{host}:{port}"
            response = await client.post(
                f"{FEED_URL}/refresh_feed",
                headers={"Authorization": raw_token}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if getattr(e, 'response', None) else 500
            detail = extract_error_detail(e, "Feed refresh error")
            raise HTTPException(status_code=status_code, detail=detail)

@app.get("/get_feed")
async def get_feed(authorization: Annotated[str | None, Header()] = None):
    # authenticate user
    await get_user_from_token(authorization)
    raw_token = authorization
    async with httpx.AsyncClient() as client:
        try:
            # use Consul-discovered endpoints for feed-service
            endpoints = find_service_endpoint('feed-service')
            host, port = random.choice(endpoints)
            FEED_URL = f"http://{host}:{port}"
            response = await client.get(
                f"{FEED_URL}/feed",
                headers={"Authorization": raw_token}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            status_code = e.response.status_code if getattr(e, 'response', None) else 500
            detail = extract_error_detail(e, "Feed fetch error")
            raise HTTPException(status_code=status_code, detail=detail)