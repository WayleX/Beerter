import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

import redis
import httpx
import consul
import random
import socket
from fastapi import FastAPI, Depends, HTTPException, Query, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

title = "Feed Service"
app = FastAPI(title=title)

# CORS
o = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=o, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

env_red = os.getenv('REDIS_HOST', 'redis')
env_rp = int(os.getenv('REDIS_PORT', 6379))
pool = redis.ConnectionPool(host=env_red, port=env_rp, decode_responses=True)

def get_redis():
    """Return a Redis client from the connection pool"""
    return redis.Redis(connection_pool=pool)

TTL = 3600

c = consul.Consul(host="consul", port=8500)

service_name = "feed-service"
service_port = int(os.getenv('SERVICE_PORT', 8000))
service_id = os.getenv('SERVICE_NAME', str(uuid.uuid4()))
port = int(os.getenv('PORT', 8000))
service_host = os.getenv('SERVICE_NAME', socket.gethostname())
print(f"Registering service {service_name} with id {service_id} on port {port}")
c.agent.service.register(
    name=service_name,
    service_id=service_name+str(service_port),
    address=service_host,
    port=port,
    check=consul.Check.http(
        url=f"http://{service_host}:{port}/health",
        interval="10s"
    )
)
print(f"Service {service_name} registered successfully")

class ReviewItem(BaseModel):
    id: str
    headline: str
    review: str
    rating: int
    product_id: str
    user_email: Optional[str]
    user_nickname: Optional[str]
    created_at: datetime
    updated_at: datetime
    liked: bool

class FeedResponse(BaseModel):
    source: str
    reviews: List[ReviewItem]

def discover(name: str):
    _, nodes = c.health.service(name, passing=True)
    return [n['Service']['Port'] for n in nodes]

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/refresh_feed", response_model=FeedResponse)
async def refresh_feed(authorization: Optional[str] = Header(None), redis_client: redis.Redis = Depends(get_redis)):
    """Refresh the feed for the user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split()[1]
    async with httpx.AsyncClient() as client:
        # Verify user
        uports = discover('beer_review_user_service')
        up = random.choice(uports)
        uurl = f"http://beer_review_user_service_{up}:{up}"
        r = await client.get(f"{uurl}/verify", headers={"Authorization": authorization})
        r.raise_for_status()
        user_info = r.json()
        # Get likes
        r2 = await client.get(f"{uurl}/likes", headers={"Authorization": authorization})
        r2.raise_for_status()
        liked_ids = r2.json()
        # Get reviews
        rports = discover('reviews-service')
        rp = random.choice(rports)
        rvurl = f"http://reviews_backend_{rp}:{rp}"
        r3 = await client.get(f"{rvurl}/reviews/")
        r3.raise_for_status()
        reviews = r3.json()
    # Pick last N by created_at and filter out already viewed
    recent = sorted(reviews, key=lambda x: x['created_at'])[-100:]
    view_key = f"views:{user_info['user_email']}"
    # fetch set of already viewed IDs
    viewed_ids = set(redis_client.smembers(view_key))
    # select only unseen reviews
    unseen = [rv for rv in recent if rv['id'] not in viewed_ids]
    # mark these as viewed
    reviews_sorted = unseen
    items = []
    for rv in reviews_sorted:
        # match likes by explicit id field
        liked = rv.get('id') in liked_ids
        items.append(ReviewItem(
            id=rv['id'],
            headline=rv['headline'],
            review=rv['review'],
            rating=rv['rating'],
            product_id=rv['product_id'],
            user_email=rv.get('user_email'),
            user_nickname=rv.get('user_nickname'),
            created_at=rv['created_at'],
            updated_at=rv['updated_at'],
            liked=liked
        ))
    # Cache
    user_key = f"feed:{user_info['user_email']}"
    redis_client.setex(user_key, TTL, json.dumps([i.dict() for i in items], default=str))
    return FeedResponse(source="fresh", reviews=items)

@app.get("/feed", response_model=FeedResponse)
async def get_feed(
    authorization: Optional[str] = Header(None),
    redis_client: redis.Redis = Depends(get_redis),
    background_tasks: BackgroundTasks = None
):
    """Get the cached feed for the user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split()[1]
    # Parse user_email from token via user service
    async with httpx.AsyncClient() as client:
        uports = discover('beer_review_user_service')
        up = random.choice(uports)
        uurl = f"http://beer_review_user_service_{up}:{up}"
        r = await client.get(f"{uurl}/verify", headers={"Authorization": authorization})
        r.raise_for_status()
        user_email = r.json().get('user_email')
    key = f"feed:{user_email}"
    data = redis_client.get(key)
    if not data:
        # Cache miss, refresh feed
        # Cache miss -> force a refresh and then reload from Redis
        await refresh_feed(authorization=authorization, redis_client=redis_client)
        data = redis_client.get(key)
        if not data:
            raise HTTPException(status_code=500, detail="Unable to refresh feed")
    items = json.loads(data)
    # return only first 3 reviews
    sliced = items[:3]
    # mark only the returned reviews as viewed
    if sliced:
        view_key = f"views:{user_email}"
        redis_client.sadd(view_key, *[i['id'] for i in sliced])
    # schedule background refresh to update cache
    if background_tasks:
        background_tasks.add_task(refresh_feed, authorization, redis_client)
    return FeedResponse(source="cache", reviews=[ReviewItem(**i) for i in sliced])

