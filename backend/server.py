from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    credits: int = 0
    total_focus_time: int = 0  # in minutes
    level: int = 1
    credit_rate_multiplier: float = 1.0  # credits per minute multiplier
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_focusing: bool = False
    current_session_start: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str

class FocusSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    credits_earned: Optional[int] = None
    is_active: bool = True

class FocusSessionStart(BaseModel):
    user_id: str

class FocusSessionEnd(BaseModel):
    user_id: str

class ShopItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: int
    item_type: str  # "boost", "sabotage", "level"
    effect: Dict[str, Any]  # JSON object describing the effect
    is_active: bool = True

class Purchase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    item_id: str
    target_user_id: Optional[str] = None  # for sabotage items
    price: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PurchaseRequest(BaseModel):
    user_id: str
    item_id: str
    target_user_id: Optional[str] = None

# ==================== USER ENDPOINTS ====================

@api_router.post("/users", response_model=User)
async def create_user(input: UserCreate):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": input.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(**input.dict())
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.get("/leaderboard", response_model=List[User])
async def get_leaderboard():
    users = await db.users.find().sort("credits", -1).limit(10).to_list(10)
    return [User(**user) for user in users]

# ==================== FOCUS SESSION ENDPOINTS ====================

@api_router.post("/focus/start", response_model=FocusSession)
async def start_focus_session(input: FocusSessionStart):
    # Check if user exists
    user = await db.users.find_one({"id": input.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user already has an active session
    active_session = await db.focus_sessions.find_one({
        "user_id": input.user_id,
        "is_active": True
    })
    if active_session:
        raise HTTPException(status_code=400, detail="User already has an active focus session")
    
    # Create new focus session
    session = FocusSession(user_id=input.user_id)
    await db.focus_sessions.insert_one(session.dict())
    
    # Update user status
    await db.users.update_one(
        {"id": input.user_id},
        {
            "$set": {
                "is_focusing": True,
                "current_session_start": session.start_time
            }
        }
    )
    
    return session

@api_router.post("/focus/end", response_model=Dict[str, Any])
async def end_focus_session(input: FocusSessionEnd):
    # Find active session
    session = await db.focus_sessions.find_one({
        "user_id": input.user_id,
        "is_active": True
    })
    if not session:
        raise HTTPException(status_code=404, detail="No active focus session found")
    
    # Get user
    user = await db.users.find_one({"id": input.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate session duration
    end_time = datetime.utcnow()
    start_time = session["start_time"]
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    
    # Calculate credits earned (base: 1 credit per minute * user's multiplier)
    base_credits = duration_minutes
    multiplier = user.get("credit_rate_multiplier", 1.0)
    credits_earned = int(base_credits * multiplier)
    
    # Update session
    await db.focus_sessions.update_one(
        {"id": session["id"]},
        {
            "$set": {
                "end_time": end_time,
                "duration_minutes": duration_minutes,
                "credits_earned": credits_earned,
                "is_active": False
            }
        }
    )
    
    # Update user credits and stats
    await db.users.update_one(
        {"id": input.user_id},
        {
            "$inc": {
                "credits": credits_earned,
                "total_focus_time": duration_minutes
            },
            "$set": {
                "is_focusing": False,
                "current_session_start": None
            }
        }
    )
    
    return {
        "session_id": session["id"],
        "duration_minutes": duration_minutes,
        "credits_earned": credits_earned,
        "total_credits": user["credits"] + credits_earned
    }

@api_router.get("/focus/active", response_model=List[User])
async def get_active_users():
    users = await db.users.find({"is_focusing": True}).to_list(1000)
    return [User(**user) for user in users]

# ==================== SHOP ENDPOINTS ====================

@api_router.get("/shop/items", response_model=List[ShopItem])
async def get_shop_items():
    items = await db.shop_items.find({"is_active": True}).to_list(1000)
    return [ShopItem(**item) for item in items]

@api_router.post("/shop/purchase", response_model=Dict[str, Any])
async def purchase_item(input: PurchaseRequest):
    # Get user
    user = await db.users.find_one({"id": input.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get shop item
    item = await db.shop_items.find_one({"id": input.item_id, "is_active": True})
    if not item:
        raise HTTPException(status_code=404, detail="Shop item not found")
    
    # Check if user has enough credits
    if user["credits"] < item["price"]:
        raise HTTPException(status_code=400, detail="Insufficient credits")
    
    # Process purchase based on item type
    if item["item_type"] == "boost":
        # Apply boost to user
        effect = item["effect"]
        update_fields = {}
        if "credit_rate_multiplier" in effect:
            new_multiplier = user.get("credit_rate_multiplier", 1.0) + effect["credit_rate_multiplier"]
            update_fields["credit_rate_multiplier"] = new_multiplier
        
        await db.users.update_one(
            {"id": input.user_id},
            {
                "$inc": {"credits": -item["price"]},
                "$set": update_fields
            }
        )
    
    elif item["item_type"] == "sabotage" and input.target_user_id:
        # Apply sabotage to target user
        target_user = await db.users.find_one({"id": input.target_user_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        
        effect = item["effect"]
        target_update = {}
        
        if "reset_credits" in effect and effect["reset_credits"]:
            target_update["credits"] = 0
        
        if "reduce_multiplier" in effect:
            current_multiplier = target_user.get("credit_rate_multiplier", 1.0)
            new_multiplier = max(0.1, current_multiplier - effect["reduce_multiplier"])
            target_update["credit_rate_multiplier"] = new_multiplier
        
        # Update target user
        await db.users.update_one(
            {"id": input.target_user_id},
            {"$set": target_update}
        )
        
        # Deduct credits from purchaser
        await db.users.update_one(
            {"id": input.user_id},
            {"$inc": {"credits": -item["price"]}}
        )
    
    # Record purchase
    purchase = Purchase(
        user_id=input.user_id,
        item_id=input.item_id,
        target_user_id=input.target_user_id,
        price=item["price"]
    )
    await db.purchases.insert_one(purchase.dict())
    
    return {
        "success": True,
        "item_name": item["name"],
        "credits_spent": item["price"],
        "target_user_id": input.target_user_id
    }

@api_router.get("/shop/purchases", response_model=List[Purchase])
async def get_recent_purchases():
    purchases = await db.purchases.find().sort("timestamp", -1).limit(20).to_list(20)
    return [Purchase(**purchase) for purchase in purchases]

# ==================== INITIALIZATION ====================

@api_router.post("/init")
async def initialize_shop_items():
    """Initialize shop with default items"""
    
    # Check if items already exist
    existing_items = await db.shop_items.count_documents({})
    if existing_items > 0:
        return {"message": "Shop items already initialized"}
    
    default_items = [
        {
            "id": str(uuid.uuid4()),
            "name": "Credit Booster",
            "description": "Increase your credit earning rate by 0.5x permanently",
            "price": 50,
            "item_type": "boost",
            "effect": {"credit_rate_multiplier": 0.5},
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Super Booster",
            "description": "Increase your credit earning rate by 1.0x permanently",
            "price": 150,
            "item_type": "boost",
            "effect": {"credit_rate_multiplier": 1.0},
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Degression Pass",
            "description": "Reduce another user's credit rate multiplier by 0.3x",
            "price": 100,
            "item_type": "sabotage",
            "effect": {"reduce_multiplier": 0.3},
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Reset Pass",
            "description": "Reset another user's credits to 0",
            "price": 200,
            "item_type": "sabotage",
            "effect": {"reset_credits": True},
            "is_active": True
        }
    ]
    
    await db.shop_items.insert_many(default_items)
    return {"message": "Shop items initialized successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()