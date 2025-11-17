"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Bioethics forum schemas

class Topic(BaseModel):
    """
    Topics users can start with a prompt. Collection: "topic"
    """
    title: str = Field(..., description="Short topic title")
    prompt: str = Field(..., description="Ethical question or prompt")
    author: Optional[str] = Field(None, description="Display name of topic creator")
    agree_count: int = Field(0, ge=0, description="Number of users who agree")
    disagree_count: int = Field(0, ge=0, description="Number of users who disagree")

class Post(BaseModel):
    """
    Posts are arguments or responses under a topic. Collection: "post"
    """
    topic_id: str = Field(..., description="ID of the parent topic")
    content: str = Field(..., description="Post body text")
    author: Optional[str] = Field(None, description="Display name of author")
    like_count: int = Field(0, ge=0, description="Number of likes on this post")

class Comment(BaseModel):
    """
    Comments under a post. Collection: "comment"
    """
    post_id: str = Field(..., description="ID of the parent post")
    content: str = Field(..., description="Comment body text")
    author: Optional[str] = Field(None, description="Display name of commenter")
    like_count: int = Field(0, ge=0, description="Number of likes on this comment")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
