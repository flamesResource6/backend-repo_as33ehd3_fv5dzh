import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Bioethics Forum API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic request models
class TopicCreate(BaseModel):
    title: str
    prompt: str
    author: Optional[str] = None

class PostCreate(BaseModel):
    topic_id: str
    content: str
    author: Optional[str] = None

class CommentCreate(BaseModel):
    post_id: str
    content: str
    author: Optional[str] = None

class VoteAction(BaseModel):
    vote: str  # "agree" | "disagree"

class LikeAction(BaseModel):
    action: str  # "like"

@app.get("/")
def read_root():
    return {"message": "Bioethics Forum Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Utility

def ensure_objectid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

# Endpoints

@app.post("/api/topics")
def create_topic(payload: TopicCreate):
    data = {
        "title": payload.title,
        "prompt": payload.prompt,
        "author": payload.author,
        "agree_count": 0,
        "disagree_count": 0,
    }
    new_id = create_document("topic", data)
    return {"id": new_id}

@app.get("/api/topics")
def list_topics():
    docs = get_documents("topic", {}, limit=100)
    # Convert ObjectId to str
    for d in docs:
        d["id"] = str(d.pop("_id"))
    # sort by updated_at desc
    docs.sort(key=lambda x: x.get("updated_at"), reverse=True)
    return docs

@app.post("/api/topics/{topic_id}/vote")
def vote_topic(topic_id: str, payload: VoteAction):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    if payload.vote not in ("agree", "disagree"):
        raise HTTPException(status_code=400, detail="Invalid vote")
    oid = ensure_objectid(topic_id)
    inc_field = "agree_count" if payload.vote == "agree" else "disagree_count"
    res = db["topic"].update_one({"_id": oid}, {"$inc": {inc_field: 1}, "$set": {"updated_at": db.command({"serverStatus":1})['localTime']}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    doc = db["topic"].find_one({"_id": oid})
    doc["id"] = str(doc.pop("_id"))
    return doc

@app.post("/api/posts")
def create_post(payload: PostCreate):
    # ensure topic exists
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    oid = ensure_objectid(payload.topic_id)
    if db["topic"].count_documents({"_id": oid}) == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    data = {
        "topic_id": str(oid),
        "content": payload.content,
        "author": payload.author,
        "like_count": 0,
    }
    new_id = create_document("post", data)
    return {"id": new_id}

@app.get("/api/topics/{topic_id}/posts")
def list_posts(topic_id: str):
    docs = get_documents("post", {"topic_id": topic_id}, limit=200)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    docs.sort(key=lambda x: x.get("updated_at"), reverse=True)
    return docs

@app.post("/api/posts/{post_id}/like")

def like_post(post_id: str, payload: LikeAction):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    if payload.action != "like":
        raise HTTPException(status_code=400, detail="Invalid action")
    oid = ensure_objectid(post_id)
    res = db["post"].update_one({"_id": oid}, {"$inc": {"like_count": 1}, "$set": {"updated_at": db.command({"serverStatus":1})['localTime']}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    doc = db["post"].find_one({"_id": oid})
    doc["id"] = str(doc.pop("_id"))
    return doc

@app.post("/api/comments")
def create_comment(payload: CommentCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    poid = ensure_objectid(payload.post_id)
    if db["post"].count_documents({"_id": poid}) == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    data = {
        "post_id": str(poid),
        "content": payload.content,
        "author": payload.author,
        "like_count": 0,
    }
    new_id = create_document("comment", data)
    return {"id": new_id}

@app.get("/api/posts/{post_id}/comments")
def list_comments(post_id: str):
    docs = get_documents("comment", {"post_id": post_id}, limit=200)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    docs.sort(key=lambda x: x.get("updated_at"), reverse=True)
    return docs

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
