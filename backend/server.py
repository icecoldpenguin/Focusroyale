from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import hashlib
from datetime import datetime, timedelta
import asyncio

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
    password_hash: str
    credits: int = 0
    total_focus_time: int = 0  # in minutes
    level: int = 1
    credit_rate_multiplier: float = 1.0  # base rate multiplier
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_focusing: bool = False
    current_session_start: Optional[datetime] = None
    active_effects: List[Dict[str, Any]] = []  # temporary effects like degression, ally tokens
    completed_tasks: int = 0

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

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

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    credits_reward: int = 3
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskCreate(BaseModel):
    title: str
    description: str

class TaskComplete(BaseModel):
    user_id: str
    task_id: str

class ShopItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: int
    emoji: str
    item_type: str  # "boost", "sabotage", "special", "level"
    effect: Dict[str, Any]  # JSON object describing the effect
    is_active: bool = True
    requires_target: bool = False
    duration_hours: Optional[int] = None  # for temporary effects

class Purchase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    item_id: str
    target_user_id: Optional[str] = None  # for sabotage/trade items
    price: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    effect_applied: bool = False
    mutual_consent: bool = False  # for trade passes

class PurchaseRequest(BaseModel):
    user_id: str
    item_id: str
    target_user_id: Optional[str] = None

class TradeConsent(BaseModel):
    user_id: str
    purchase_id: str
    consent: bool

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    notification_type: str  # "pass_used", "task_completed", "trade_request", etc.
    related_user_id: Optional[str] = None
    is_read: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

async def calculate_effective_credit_rate(user_data: dict) -> float:
    """Calculate user's current effective credit rate including temporary effects"""
    base_rate = user_data.get("credit_rate_multiplier", 1.0)
    effective_rate = base_rate
    
    # Check for active effects
    active_effects = user_data.get("active_effects", [])
    current_time = datetime.utcnow()
    
    for effect in active_effects:
        if effect.get("expires_at") and datetime.fromisoformat(effect["expires_at"]) > current_time:
            if effect["type"] == "degression":
                effective_rate -= effect.get("rate_reduction", 0.5)
            elif effect["type"] == "ally_boost":
                effective_rate += effect.get("rate_boost", 1.0)
    
    return max(0.1, effective_rate)  # Minimum rate of 0.1

async def clean_expired_effects():
    """Remove expired effects from all users"""
    current_time = datetime.utcnow()
    await db.users.update_many(
        {},
        {
            "$pull": {
                "active_effects": {
                    "expires_at": {"$lt": current_time.isoformat()}
                }
            }
        }
    )

# ==================== AUTHENTICATION ENDPOINTS ====================

@api_router.post("/auth/register", response_model=Dict[str, Any])
async def register_user(input: UserRegister):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": input.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    user = User(
        username=input.username,
        password_hash=hash_password(input.password)
    )
    await db.users.insert_one(user.dict())
    
    # Return user without password hash
    user_dict = user.dict()
    del user_dict['password_hash']
    return {"user": user_dict, "message": "User registered successfully"}

@api_router.post("/auth/login", response_model=Dict[str, Any])
async def login_user(input: UserLogin):
    # Find user
    user = await db.users.find_one({"username": input.username})
    if not user or not verify_password(input.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Clean expired effects
    await clean_expired_effects()
    
    # Update user data after cleaning effects
    updated_user = await db.users.find_one({"id": user["id"]})
    
    # Return user without password hash
    user_dict = User(**updated_user).dict()
    del user_dict['password_hash']
    return {"user": user_dict, "message": "Login successful"}

# ==================== USER ENDPOINTS ====================

@api_router.get("/users", response_model=List[Dict[str, Any]])
async def get_users():
    await clean_expired_effects()
    users = await db.users.find().to_list(1000)
    # Convert ObjectId to string and remove password hashes
    result = []
    for user in users:
        user_dict = dict(user)
        if '_id' in user_dict:
            del user_dict['_id']  # Remove MongoDB _id field
        if 'password_hash' in user_dict:
            del user_dict['password_hash']
        result.append(user_dict)
    return result

@api_router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user(user_id: str):
    await clean_expired_effects()
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove MongoDB _id and password hash from response
    user_dict = dict(user)
    if '_id' in user_dict:
        del user_dict['_id']
    if 'password_hash' in user_dict:
        del user_dict['password_hash']
    return user_dict

@api_router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard():
    await clean_expired_effects()
    users = await db.users.find().sort("credits", -1).limit(10).to_list(10)
    # Convert ObjectId to string and remove password hashes
    result = []
    for user in users:
        user_dict = dict(user)
        if '_id' in user_dict:
            del user_dict['_id']
        if 'password_hash' in user_dict:
            del user_dict['password_hash']
        result.append(user_dict)
    return result

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
    
    # Calculate credits earned (10 credits per hour = 1 credit per 6 minutes)
    # So credits = duration_minutes / 6 * effective_rate
    base_credits_per_hour = 10
    minutes_per_credit = 60 / base_credits_per_hour  # 6 minutes per credit
    
    effective_rate = await calculate_effective_credit_rate(user)
    credits_earned = int((duration_minutes / minutes_per_credit) * effective_rate)
    
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
        "total_credits": user["credits"] + credits_earned,
        "effective_rate": effective_rate
    }

@api_router.get("/focus/active", response_model=List[Dict[str, Any]])
async def get_active_users():
    await clean_expired_effects()
    users = await db.users.find({"is_focusing": True}).to_list(1000)
    # Convert ObjectId to string and remove password hashes
    result = []
    for user in users:
        user_dict = dict(user)
        if '_id' in user_dict:
            del user_dict['_id']
        if 'password_hash' in user_dict:
            del user_dict['password_hash']
        result.append(user_dict)
    return result

# ==================== TASKS ENDPOINTS ====================

@api_router.post("/tasks", response_model=Task)
async def create_task(input: TaskCreate):
    task = Task(**input.dict())
    await db.tasks.insert_one(task.dict())
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks():
    tasks = await db.tasks.find({"is_active": True}).to_list(1000)
    return [Task(**task) for task in tasks]

@api_router.post("/tasks/complete", response_model=Dict[str, Any])
async def complete_task(input: TaskComplete):
    # Get user and task
    user = await db.users.find_one({"id": input.user_id})
    task = await db.tasks.find_one({"id": input.task_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Award credits and update user
    credits_earned = task.get("credits_reward", 3)
    await db.users.update_one(
        {"id": input.user_id},
        {
            "$inc": {
                "credits": credits_earned,
                "completed_tasks": 1
            }
        }
    )
    
    # Create notification for activity feed
    notification = Notification(
        user_id="system",  # System notification for all to see
        message=f"{user['username']} has completed the task '{task['title']}'",
        notification_type="task_completed",
        related_user_id=input.user_id
    )
    await db.notifications.insert_one(notification.dict())
    
    return {
        "success": True,
        "credits_earned": credits_earned,
        "task_title": task["title"],
        "total_credits": user["credits"] + credits_earned
    }

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
    
    # Check if target is required but not provided
    if item.get("requires_target", False) and not input.target_user_id:
        raise HTTPException(status_code=400, detail="Target user required for this item")
    
    # Get target user if specified
    target_user = None
    if input.target_user_id:
        target_user = await db.users.find_one({"id": input.target_user_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
    
    # Process purchase based on item type
    effect_applied = True
    mutual_consent_required = False
    
    if item["item_type"] == "level":
        # Level Pass - increase user level
        await db.users.update_one(
            {"id": input.user_id},
            {
                "$inc": {"credits": -item["price"], "level": 1}
            }
        )
        
    elif item["item_type"] == "boost":
        # Progression Pass - permanent credit rate increase
        effect = item["effect"]
        if "credit_rate_multiplier" in effect:
            await db.users.update_one(
                {"id": input.user_id},
                {
                    "$inc": {
                        "credits": -item["price"],
                        "credit_rate_multiplier": effect["credit_rate_multiplier"]
                    }
                }
            )
    
    elif item["item_type"] == "sabotage" and target_user:
        effect = item["effect"]
        
        if "reset_credits" in effect and effect["reset_credits"]:
            # Reset Pass - reset target's credits
            await db.users.update_one(
                {"id": input.target_user_id},
                {"$set": {"credits": 0}}
            )
        
        elif "rate_reduction" in effect:
            # Degression Pass - temporary rate reduction
            expires_at = datetime.utcnow() + timedelta(hours=item.get("duration_hours", 24))
            degression_effect = {
                "type": "degression",
                "rate_reduction": effect["rate_reduction"],
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
            
            await db.users.update_one(
                {"id": input.target_user_id},
                {"$push": {"active_effects": degression_effect}}
            )
        
        # Deduct credits from purchaser
        await db.users.update_one(
            {"id": input.user_id},
            {"$inc": {"credits": -item["price"]}}
        )
        
        # Create notification for target
        notification = Notification(
            user_id=input.target_user_id,
            message=f"{user['username']} used {item['name']} on you!",
            notification_type="pass_used",
            related_user_id=input.user_id
        )
        await db.notifications.insert_one(notification.dict())
    
    elif item["item_type"] == "special":
        if "ally_boost" in item["effect"]:
            # Ally Token - both users get boost
            if not target_user:
                raise HTTPException(status_code=400, detail="Target user required for ally token")
            
            expires_at = datetime.utcnow() + timedelta(hours=item.get("duration_hours", 3))
            ally_effect = {
                "type": "ally_boost",
                "rate_boost": item["effect"]["ally_boost"],
                "expires_at": expires_at.isoformat(),
                "ally_id": input.target_user_id if target_user else input.user_id
            }
            
            # Apply effect to both users
            await db.users.update_one(
                {"id": input.user_id},
                {
                    "$inc": {"credits": -item["price"]},
                    "$push": {"active_effects": ally_effect}
                }
            )
            
            ally_effect_target = ally_effect.copy()
            ally_effect_target["ally_id"] = input.user_id
            await db.users.update_one(
                {"id": input.target_user_id},
                {"$push": {"active_effects": ally_effect_target}}
            )
            
            # Notify target
            notification = Notification(
                user_id=input.target_user_id,
                message=f"{user['username']} formed a Focus Link with you! Both earning +1x for 3 hours",
                notification_type="ally_formed",
                related_user_id=input.user_id
            )
            await db.notifications.insert_one(notification.dict())
        
        elif "trade_request" in item["effect"]:
            # Trade Pass - requires mutual consent
            mutual_consent_required = True
            effect_applied = False
    
    # Record purchase
    purchase = Purchase(
        user_id=input.user_id,
        item_id=input.item_id,
        target_user_id=input.target_user_id,
        price=item["price"],
        effect_applied=effect_applied,
        mutual_consent=mutual_consent_required
    )
    await db.purchases.insert_one(purchase.dict())
    
    # Create activity notification
    if target_user and item["item_type"] in ["sabotage", "special"]:
        activity_msg = f"{user['username']} used {item['name']} on {target_user['username']}"
    else:
        activity_msg = f"{user['username']} purchased {item['name']}"
    
    activity_notification = Notification(
        user_id="system",
        message=activity_msg,
        notification_type="purchase",
        related_user_id=input.user_id
    )
    await db.notifications.insert_one(activity_notification.dict())
    
    return {
        "success": True,
        "item_name": item["name"],
        "credits_spent": item["price"],
        "target_user_id": input.target_user_id,
        "requires_consent": mutual_consent_required,
        "purchase_id": purchase.id if mutual_consent_required else None
    }

# ==================== NOTIFICATIONS ENDPOINTS ====================

@api_router.get("/notifications/{user_id}", response_model=List[Notification])
async def get_user_notifications(user_id: str):
    notifications = await db.notifications.find({
        "$or": [
            {"user_id": user_id},
            {"user_id": "system"}
        ]
    }).sort("timestamp", -1).limit(50).to_list(50)
    return [Notification(**notif) for notif in notifications]

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"is_read": True}}
    )
    return {"success": True}

# ==================== ADMIN/UTILITY ENDPOINTS ====================

@api_router.post("/admin/reset-database")
async def reset_database():
    """Reset database - remove all users, sessions, purchases, notifications"""
    await db.users.delete_many({})
    await db.focus_sessions.delete_many({})
    await db.purchases.delete_many({})
    await db.notifications.delete_many({})
    await db.tasks.delete_many({})
    return {"message": "Database reset successfully"}

@api_router.post("/init")
async def initialize_shop_items():
    """Initialize shop with new pass system"""
    
    # Reset shop items
    await db.shop_items.delete_many({})
    
    new_items = [
        {
            "id": str(uuid.uuid4()),
            "name": "Level Pass",
            "description": "Move up 1 Level (unlocks prestige perks, leaderboard advantage, or visual flex)",
            "emoji": "🎟️",
            "price": 100,
            "item_type": "level",
            "effect": {"level_increase": 1},
            "is_active": True,
            "requires_target": False
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Progression Pass",
            "description": "Increase your credit/hr rate by +0.5x permanently",
            "emoji": "⚡",
            "price": 80,
            "item_type": "boost",
            "effect": {"credit_rate_multiplier": 0.5},
            "is_active": True,
            "requires_target": False
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Degression Pass",
            "description": "Select someone → their credit rate is reduced by -0.5x for 24 hours",
            "emoji": "💀",
            "price": 120,
            "item_type": "sabotage",
            "effect": {"rate_reduction": 0.5},
            "is_active": True,
            "requires_target": True,
            "duration_hours": 24
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Reset Pass",
            "description": "Reset another player's FC to 0 — yes, full wipeout. Use with caution (or pure rage)",
            "emoji": "🔥",
            "price": 500,
            "item_type": "sabotage",
            "effect": {"reset_credits": True},
            "is_active": True,
            "requires_target": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Ally Token",
            "description": "Forms a 'Focus Link' with a chosen player: both get +1x extra credit rate for 3 hours",
            "emoji": "🤝",
            "price": 60,
            "item_type": "special",
            "effect": {"ally_boost": 1.0},
            "is_active": True,
            "requires_target": True,
            "duration_hours": 3
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Trade Pass",
            "description": "Trade FC with another player (needs mutual consent)",
            "emoji": "🔄",
            "price": 50,
            "item_type": "special",
            "effect": {"trade_request": True},
            "is_active": True,
            "requires_target": True
        }
    ]
    
    await db.shop_items.insert_many(new_items)
    
    # Initialize some sample tasks
    sample_tasks = [
        {
            "id": str(uuid.uuid4()),
            "title": "Read for 30 minutes",
            "description": "Complete a 30-minute focused reading session",
            "credits_reward": 3,
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Exercise workout",
            "description": "Complete a workout or physical exercise session",
            "credits_reward": 3,
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Learn something new",
            "description": "Spend time learning a new skill or topic",
            "credits_reward": 3,
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Organize workspace",
            "description": "Clean and organize your work area",
            "credits_reward": 3,
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Plan your day",
            "description": "Create a detailed plan for your daily activities",
            "credits_reward": 3,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    await db.tasks.insert_many(sample_tasks)
    
    return {"message": "Shop items and tasks initialized successfully"}

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