from fastapi import FastAPI, HTTPException, Query, Header
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
import os
import httpx
from datetime import datetime
import consul
import random

app = FastAPI()

# MongoDB Connection
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:password@mongodb:27017/")
MONGO_DB = os.environ.get("MONGO_DB", "reviews_db")
port = int(os.environ.get("PORT", 8000))
c = consul.Consul(host="consul", port=8500)

service_name = "reviews-service"
c.agent.service.register(
    name=service_name,
    service_id=service_name + str(port),
    port=port,

    check=consul.Check.http(
        url = f"http://reviews_backend_{port}:{port}/",
        interval="10s"
        
    )
)


# Register the service with Consul
# MongoDB client connection
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
reviews_collection = db["reviews"]


# Ensure text index exists on headline and review, create if missing
indexes = [idx['key'] for idx in reviews_collection.list_indexes()]
text_index_exists = any(
    ("headline", "text") in idx.items() or ("review", "text") in idx.items()
    for idx in indexes
)
if not text_index_exists:
    reviews_collection.create_index([("headline", "text"), ("review", "text")])
# # Drop any existing text index to avoid conflicts
# for idx in reviews_collection.list_indexes():
#     if idx.get('key') == {'_fts': 'text', '_ftsx': 1}:
#         reviews_collection.drop_index(idx['name'])
#         break
# # Create new text index on headline and review
# reviews_collection.create_index([("headline", "text"), ("review", "text")])

class reviewModel(BaseModel):
    headline: str
    review: str
    rating: int
    product_id: str
    user_email: Optional[str] = None  # attached by facade
    user_nickname: Optional[str] = None  # attached by facade

class updateModel(BaseModel):
    headline: Optional[str] = None
    review: Optional[str] = None
    rating: Optional[int] = None
    product_id: Optional[str] = None

def serialize_doc(doc):
    if not doc:
        return doc
    doc["_id"] = str(doc["_id"])
    # add explicit id field for client-side use
    doc["id"] = doc["_id"]
    return doc

# Helper: get liked posts for a user
async def get_user_likes(authorization: str):
    # discover user-service via Consul
    _, nodes = c.health.service('beer_review_user_service', passing=True)
    ports = [n['Service']['Port'] for n in nodes]
    port = random.choice(ports)
    user_url = f"http://beer_review_user_service_{port}:{port}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{user_url}/likes", headers={"Authorization": authorization})
        resp.raise_for_status()
        return resp.json()

# Routes
@app.get("/")
def read_root():
    return {"message": "Reviews API"}

@app.post("/reviews/")
async def create_review(review: reviewModel):
    print("LOG: Creating review:", review.model_dump_json())
    now = datetime.utcnow()
    review_dict = review.dict()
    review_dict["created_at"] = now
    review_dict["updated_at"] = now
    
    result = reviews_collection.insert_one(review_dict)
    created_review = reviews_collection.find_one({"_id": result.inserted_id})
    
    return serialize_doc(created_review)

@app.get("/reviews/")
async def list_reviews(authorization: Optional[str] = Header(None)):
    # fetch all reviews and annotate liked status
    results = list(reviews_collection.find())
    docs = [serialize_doc(i) for i in results]
    liked_ids = []
    if authorization and authorization.startswith("Bearer "):
        liked_ids = await get_user_likes(authorization)
    for d in docs:
        d['liked'] = d.get('id') in liked_ids
    return docs

@app.get("/reviews/{review_id}")
async def get_review(review_id: str, authorization: Optional[str] = Header(None)):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status_code=400, detail="Invalid review ID")
    review = reviews_collection.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    doc = serialize_doc(review)
    # annotate liked status for this review
    if authorization and authorization.startswith("Bearer "):
        liked_ids = await get_user_likes(authorization)
        doc['liked'] = doc.get('id') in liked_ids
    else:
        doc['liked'] = False
    return doc

@app.put("/reviews/{review_id}")
async def update_review(
    review_id: str,
    review_update: updateModel,
    authorization: Optional[str] = Header(None)
):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status_code=400, detail="Invalid review ID")
    # authenticate and get user_email
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    # verify with User service
    _, nodes = c.health.service('beer_review_user_service', passing=True)
    ports = [n['Service']['Port'] for n in nodes]
    up = random.choice(ports)
    user_url = f"http://beer_review_user_service_{up}:{up}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{user_url}/verify", headers={"Authorization": authorization})
        resp.raise_for_status()
        user_email = resp.json().get('user_email')
    # fetch existing review
    existing = reviews_collection.find_one({"_id": ObjectId(review_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Review not found")
    # authorization check
    if existing.get('user_email') != user_email:
        raise HTTPException(status_code=403, detail="Not allowed to edit this review")
    
    # Get only the set fields from update
    update_data = {k: v for k, v in review_update.dict(exclude_unset=True).items()}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Add updated_at field
    update_data["updated_at"] = datetime.utcnow()
    
    result = reviews_collection.update_one(
        {"_id": ObjectId(review_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
        
    updated_review = reviews_collection.find_one({"_id": ObjectId(review_id)})
    return serialize_doc(updated_review)

@app.delete("/reviews/{review_id}")
async def delete_review(review_id: str):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(status_code=400, detail="Invalid review ID")
        
    result = reviews_collection.delete_one({"_id": ObjectId(review_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
        
    return {"message": "Review deleted successfully"}

@app.get("/reviews/search/")
async def search_reviews(q: str = Query(..., min_length=1, description="Search query"), authorization: Optional[str] = Header(None)):
    results = list(reviews_collection.find({"$text": {"$search": q}}))
    docs = [serialize_doc(i) for i in results]
    liked_ids = []
    if authorization:
        liked_ids = await get_user_likes(authorization)
    for d in docs:
        d['liked'] = d['id'] in liked_ids
    return docs

@app.get("/reviews/keyword/{keyword}")
async def search_by_keyword(keyword: str, authorization: Optional[str] = Header(None)):
    # search for keyword in headline or review text
    results = list(reviews_collection.find({
        "$or": [
            {"headline": {"$regex": keyword, "$options": "i"}},
            {"review": {"$regex": keyword, "$options": "i"}}
        ]
    }))
    docs = [serialize_doc(i) for i in results]
    liked_ids = []
    if authorization:
        liked_ids = await get_user_likes(authorization)
    for d in docs:
        d['liked'] = d['id'] in liked_ids
    return docs