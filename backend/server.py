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
import bcrypt

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
    bio: str = ""
    profile_picture: str = ""
    last_wheel_spin: Optional[datetime] = None  # tracks daily wheel spin

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    user_id: str
    username: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

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
    user_id: str  # Owner of the task
    title: str
    description: str
    credits_reward: int = 10
    is_active: bool = True
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskCreate(BaseModel):
    user_id: str
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

class WeeklyTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    tags: List[str] = []
    day_of_week: int  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    week_start: datetime  # Start of the week this task belongs to
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class WeeklyTaskCreate(BaseModel):
    user_id: str
    title: str
    description: str
    tags: List[str] = []
    day_of_week: int

class WeeklyTaskComplete(BaseModel):
    user_id: str
    task_id: str

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    notification_type: str  # "pass_used", "task_completed", "trade_request", etc.
    related_user_id: Optional[str] = None
    is_read: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TradeRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requester_id: str
    target_id: str
    requester_credits: int
    target_credits: int
    status: str = "pending"  # "pending", "accepted", "rejected", "expired"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))

class TradeRequestCreate(BaseModel):
    target_user_id: str
    offered_credits: int
    requested_credits: int

class TradeResponse(BaseModel):
    trade_request_id: str
    response: str  # "accept" or "reject"

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

async def calculate_effective_credit_rate(user_data: dict) -> float:
    """Calculate user's current effective credit rate including temporary effects and social multiplier"""
    base_rate = user_data.get("credit_rate_multiplier", 1.0)
    effective_rate = base_rate
    
    # Get social multiplier based on number of active focusing users
    active_users_count = await db.users.count_documents({"is_focusing": True})
    social_multiplier = max(1.0, float(active_users_count))  # Minimum 1.0x if no one is focusing
    
    # Check for temporary effects
    active_effects = user_data.get("active_effects", [])
    current_time = datetime.utcnow()
    
    # Check for immunity first - blocks negative effects
    has_immunity = False
    for effect in active_effects:
        if (effect.get("expires_at") and datetime.fromisoformat(effect["expires_at"]) > current_time and 
            effect.get("type") == "immunity_shield"):
            has_immunity = True
            break
    
    # Check for dominance effect first - overrides social multiplier
    dominance_active = False
    for effect in active_effects:
        if (effect.get("expires_at") and datetime.fromisoformat(effect["expires_at"]) > current_time and 
            effect.get("type") == "global_dominance"):
            dominance_active = True
            break
    
    for effect in active_effects:
        if effect.get("expires_at") and datetime.fromisoformat(effect["expires_at"]) > current_time:
            if effect["type"] == "degression" and not has_immunity:
                # Halve the effective rate
                effective_rate = effective_rate * 0.5
            elif effect["type"] == "ally_boost":
                effective_rate += effect.get("rate_boost", 1.0)
            elif effect["type"] == "dominance_reduced" and not dominance_active:
                # User is affected by someone else's dominance
                effective_rate = effective_rate * 0.5
            elif effect["type"] == "inversion_swap":
                # Use the swapped multiplier instead of original
                effective_rate = effect.get("swapped_multiplier", base_rate)
    
    # Apply social multiplier to final rate (unless dominance is active for this user)
    final_rate = max(0.1, effective_rate) * social_multiplier
    
    return final_rate

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
    
    # Return user without password hash and MongoDB _id
    user_dict = user.dict()
    if '_id' in user_dict:
        del user_dict['_id']
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
    
    # Return user without password hash and MongoDB _id
    user_dict = dict(updated_user)
    if '_id' in user_dict:
        del user_dict['_id']
    if 'password_hash' in user_dict:
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

@api_router.put("/users/update", response_model=Dict[str, Any])
async def update_user(input: UserUpdate):
    """Update user profile information including username, bio, profile picture, and password"""
    # Check if user exists
    user = await db.users.find_one({"id": input.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    
    # Handle username update
    if input.username and input.username.strip() != user.get('username'):
        new_username = input.username.strip()
        # Check if username is already taken by another user
        existing_user = await db.users.find_one({"username": new_username, "id": {"$ne": input.user_id}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_data["username"] = new_username
    
    # Handle bio update
    if input.bio is not None:
        update_data["bio"] = input.bio.strip()
    
    # Handle profile picture update
    if input.profile_picture is not None:
        update_data["profile_picture"] = input.profile_picture
    
    # Handle password update
    if input.current_password and input.new_password:
        # Verify current password
        if not bcrypt.checkpw(input.current_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(input.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_data["password_hash"] = new_password_hash
    
    # Update user in database
    if update_data:
        await db.users.update_one({"id": input.user_id}, {"$set": update_data})
    
    # Return updated user data
    updated_user = await db.users.find_one({"id": input.user_id})
    user_dict = dict(updated_user)
    if '_id' in user_dict:
        del user_dict['_id']
    if 'password_hash' in user_dict:
        del user_dict['password_hash']
    
    return {"message": "User updated successfully", "user": user_dict}

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
    
    # Calculate credits earned (30 credits per hour = 1 credit per 2 minutes)
    # So credits = duration_minutes / 2 * effective_rate
    base_credits_per_hour = 30
    minutes_per_credit = 60 / base_credits_per_hour  # 2 minutes per credit
    
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

@api_router.get("/focus/social-rate", response_model=Dict[str, Any])
async def get_social_rate():
    """Get current social multiplier based on active users"""
    await clean_expired_effects()
    active_users_count = await db.users.count_documents({"is_focusing": True})
    social_multiplier = max(1.0, float(active_users_count))
    
    return {
        "active_users_count": active_users_count,
        "social_multiplier": social_multiplier,
        "credits_per_hour": social_multiplier * 30,  # Base 30 credits/hour * multiplier
        "description": f"{active_users_count} users focusing = {social_multiplier}x rate = {social_multiplier * 30} credits/hour"
    }

# ==================== TASKS ENDPOINTS ====================

@api_router.post("/tasks", response_model=Task)
async def create_task(input: TaskCreate):
    task = Task(**input.dict())
    await db.tasks.insert_one(task.dict())
    return task

@api_router.get("/tasks/{user_id}", response_model=List[Task])
async def get_user_tasks(user_id: str):
    tasks = await db.tasks.find({"user_id": user_id, "is_active": True, "is_completed": False}).to_list(1000)
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
    
    # Check if task belongs to user
    if task["user_id"] != input.user_id:
        raise HTTPException(status_code=403, detail="You can only complete your own tasks")
    
    # Check if task is already completed
    if task.get("is_completed", False):
        raise HTTPException(status_code=400, detail="Task is already completed")
    
    # Mark task as completed
    await db.tasks.update_one(
        {"id": input.task_id},
        {"$set": {"is_completed": True}}
    )
    
    # Check for Assassin Pass effect - 0 credits for next 3 tasks
    credits_earned = task.get("credits_reward", 10)
    assassin_active = False
    
    # Clean expired effects first
    await clean_expired_effects()
    # Get updated user data
    user = await db.users.find_one({"id": input.user_id})
    
    active_effects = user.get("active_effects", [])
    current_time = datetime.utcnow()
    
    for i, effect in enumerate(active_effects):
        if (effect.get("expires_at") and datetime.fromisoformat(effect["expires_at"]) > current_time and
            effect.get("type") == "assassin_curse" and effect.get("tasks_remaining", 0) > 0):
            
            # Assassin effect is active - no credits for this task
            credits_earned = 0
            assassin_active = True
            
            # Decrease tasks remaining
            remaining = effect.get("tasks_remaining", 1) - 1
            if remaining <= 0:
                # Remove the effect if no more tasks affected
                await db.users.update_one(
                    {"id": input.user_id},
                    {"$pull": {"active_effects": {"type": "assassin_curse", "tasks_remaining": {"$lte": 1}}}}
                )
            else:
                # Update the remaining count
                await db.users.update_one(
                    {"id": input.user_id, "active_effects.type": "assassin_curse"},
                    {"$set": {"active_effects.$.tasks_remaining": remaining}}
                )
            break
    
    # Award credits and update user
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
    message = f"{user['username']} has completed the task '{task['title']}'"
    if assassin_active:
        message += " (No credits due to Assassin curse)"
    
    notification = Notification(
        user_id="system",  # System notification for all to see
        message=message,
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
    
    # Check if user is frozen (can't use passes)
    await clean_expired_effects()
    user = await db.users.find_one({"id": input.user_id})  # Refresh user data
    
    active_effects = user.get("active_effects", [])
    current_time = datetime.utcnow()
    
    for effect in active_effects:
        if (effect.get("expires_at") and datetime.fromisoformat(effect["expires_at"]) > current_time and
            effect.get("type") == "freeze_passes"):
            raise HTTPException(status_code=400, detail="You are frozen and cannot use any passes!")
    
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
        elif "time_loop" in effect and effect["time_loop"]:
            # Time Loop Pass - repeat last hour's credit gain
            # Calculate last hour credits gained from focus sessions
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_sessions = await db.focus_sessions.find({
                "user_id": input.user_id,
                "end_time": {"$exists": True},
                "end_time": {"$gte": one_hour_ago.isoformat()}
            }).to_list(1000)
            
            total_recent_credits = sum(session.get("credits_earned", 0) for session in recent_sessions)
            
            # Award the same amount of credits again
            await db.users.update_one(
                {"id": input.user_id},
                {
                    "$inc": {
                        "credits": -item["price"] + total_recent_credits
                    }
                }
            )
            
            # Create notification
            notification = Notification(
                user_id=input.user_id,
                message=f"Time Loop activated! Gained {total_recent_credits} FC from repeating last hour's progress",
                notification_type="time_loop",
                related_user_id=input.user_id
            )
            await db.notifications.insert_one(notification.dict())
    
    elif item["item_type"] == "defensive":
        # Defensive passes - Mirror and Immunity
        effect = item["effect"]
        expires_at = datetime.utcnow() + timedelta(hours=item.get("duration_hours", 24))
        
        if "mirror_shield" in effect and effect["mirror_shield"]:
            # Mirror Pass - reflects next pass back
            mirror_effect = {
                "type": "mirror_shield",
                "active": True,
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
        elif "immunity_shield" in effect and effect["immunity_shield"]:
            # Immunity Pass - blocks all negative passes
            mirror_effect = {
                "type": "immunity_shield",
                "active": True,
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
        
        await db.users.update_one(
            {"id": input.user_id},
            {
                "$inc": {"credits": -item["price"]},
                "$push": {"active_effects": mirror_effect}
            }
        )
    
    elif item["item_type"] == "sabotage" and target_user:
        effect = item["effect"]
        
        # Check if target has immunity or mirror shield
        target_effects = target_user.get("active_effects", [])
        current_time = datetime.utcnow()
        
        has_immunity = False
        has_mirror = False
        
        for target_effect in target_effects:
            if (target_effect.get("expires_at") and datetime.fromisoformat(target_effect["expires_at"]) > current_time):
                if target_effect.get("type") == "immunity_shield":
                    has_immunity = True
                    break
                elif target_effect.get("type") == "mirror_shield":
                    has_mirror = True
                    
                    # Remove the mirror shield (one-time use)
                    await db.users.update_one(
                        {"id": input.target_user_id},
                        {"$pull": {"active_effects": {"type": "mirror_shield"}}}
                    )
                    break
        
        # If target has immunity, block the attack completely
        if has_immunity:
            # Still deduct credits from attacker but no effect on target
            await db.users.update_one(
                {"id": input.user_id},
                {"$inc": {"credits": -item["price"]}}
            )
            
            # Notify target they were protected
            notification = Notification(
                user_id=input.target_user_id,
                message=f"Your Immunity Shield blocked {user['username']}'s {item['name']}!",
                notification_type="immunity_blocked",
                related_user_id=input.user_id
            )
            await db.notifications.insert_one(notification.dict())
            
            return {
                "success": True,
                "item_name": item["name"],
                "credits_spent": item["price"],
                "target_user_id": input.target_user_id,
                "requires_consent": False,
                "message": f"Attack blocked by {target_user['username']}'s Immunity Shield!"
            }
        
        # If target has mirror shield, reflect the attack back
        elif has_mirror:
            # Apply the effect to the attacker instead
            actual_target_id = input.user_id
            actual_target = user
        else:
            # Normal attack
            actual_target_id = input.target_user_id
            actual_target = target_user
        
        if "reset_credits" in effect and effect["reset_credits"]:
            # Reset Pass - reset target's credits
            await db.users.update_one(
                {"id": actual_target_id},
                {"$set": {"credits": 0}}
            )
            
            if has_mirror:
                # Notify about reflection
                notification = Notification(
                    user_id=input.user_id,
                    message=f"{target_user['username']}'s Mirror Shield reflected your {item['name']} back at you!",
                    notification_type="mirror_reflected",
                    related_user_id=input.target_user_id
                )
                await db.notifications.insert_one(notification.dict())
        
        elif "rate_halved" in effect or "rate_reduction" in effect:
            # Degression Pass - temporary rate halving effect
            expires_at = datetime.utcnow() + timedelta(hours=item.get("duration_hours", 24))
            degression_effect = {
                "type": "degression",
                "rate_halved": True,
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
            
            await db.users.update_one(
                {"id": actual_target_id},
                {"$push": {"active_effects": degression_effect}}
            )
            
            if has_mirror:
                notification = Notification(
                    user_id=input.user_id,
                    message=f"{target_user['username']}'s Mirror Shield reflected your {item['name']} back at you!",
                    notification_type="mirror_reflected",
                    related_user_id=input.target_user_id
                )
                await db.notifications.insert_one(notification.dict())
        
        elif "global_dominance" in effect and effect["global_dominance"]:
            # Dominance Pass - all other players earn 50% credits
            expires_at = datetime.utcnow() + timedelta(hours=item.get("duration_hours", 1))
            dominance_effect = {
                "type": "global_dominance",
                "active": True,
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
            
            # Apply dominance effect to the purchaser (they are immune)
            await db.users.update_one(
                {"id": input.user_id},
                {"$push": {"active_effects": dominance_effect}}
            )
            
            # Apply reduced earning effect to ALL other users
            all_other_users = await db.users.find({"id": {"$ne": input.user_id}}).to_list(1000)
            for other_user in all_other_users:
                reduced_effect = {
                    "type": "dominance_reduced",
                    "credit_multiplier": 0.5,
                    "expires_at": expires_at.isoformat(),
                    "applied_by": input.user_id
                }
                await db.users.update_one(
                    {"id": other_user["id"]},
                    {"$push": {"active_effects": reduced_effect}}
                )
        
        elif "assassin_curse" in effect and effect["assassin_curse"]:
            # Assassin Pass - 0 credits for next 3 tasks
            expires_at = datetime.utcnow() + timedelta(hours=item.get("duration_hours", 24))
            assassin_effect = {
                "type": "assassin_curse",
                "tasks_remaining": effect.get("tasks_affected", 3),
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
            
            await db.users.update_one(
                {"id": actual_target_id},
                {"$push": {"active_effects": assassin_effect}}
            )
            
            if has_mirror:
                notification = Notification(
                    user_id=input.user_id,
                    message=f"{target_user['username']}'s Mirror Shield reflected your {item['name']} back at you!",
                    notification_type="mirror_reflected",
                    related_user_id=input.target_user_id
                )
                await db.notifications.insert_one(notification.dict())
        
        elif "freeze_passes" in effect and effect["freeze_passes"]:
            # Freeze Pass - can't use passes for 12 hours
            expires_at = datetime.utcnow() + timedelta(hours=item.get("duration_hours", 12))
            freeze_effect = {
                "type": "freeze_passes",
                "active": True,
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
            
            await db.users.update_one(
                {"id": actual_target_id},
                {"$push": {"active_effects": freeze_effect}}
            )
            
            if has_mirror:
                notification = Notification(
                    user_id=input.user_id,
                    message=f"{target_user['username']}'s Mirror Shield reflected your {item['name']} back at you!",
                    notification_type="mirror_reflected",
                    related_user_id=input.target_user_id
                )
                await db.notifications.insert_one(notification.dict())
        
        # Deduct credits from purchaser
        await db.users.update_one(
            {"id": input.user_id},
            {"$inc": {"credits": -item["price"]}}
        )
        
        # Create notification for target (unless it was reflected)
        if not has_mirror:
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
        
        elif "inversion_swap" in item["effect"] and target_user:
            # Inversion Pass - swap credit rate multipliers
            if not target_user:
                raise HTTPException(status_code=400, detail="Target user required for inversion")
            
            # Get current multipliers
            user_multiplier = user.get("credit_rate_multiplier", 1.0)
            target_multiplier = target_user.get("credit_rate_multiplier", 1.0)
            
            # Create temporary swap effects for both users
            expires_at = datetime.utcnow() + timedelta(hours=item.get("duration_hours", 1))
            
            # Effect for the purchaser (gets target's multiplier)
            purchaser_effect = {
                "type": "inversion_swap",
                "swapped_multiplier": target_multiplier,
                "original_multiplier": user_multiplier,
                "swap_partner": input.target_user_id,
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
            
            # Effect for the target (gets purchaser's multiplier)
            target_effect = {
                "type": "inversion_swap",
                "swapped_multiplier": user_multiplier,
                "original_multiplier": target_multiplier,
                "swap_partner": input.user_id,
                "expires_at": expires_at.isoformat(),
                "applied_by": input.user_id
            }
            
            # Apply effects to both users
            await db.users.update_one(
                {"id": input.user_id},
                {
                    "$inc": {"credits": -item["price"]},
                    "$push": {"active_effects": purchaser_effect}
                }
            )
            
            await db.users.update_one(
                {"id": input.target_user_id},
                {"$push": {"active_effects": target_effect}}
            )
            
            # Notify target
            notification = Notification(
                user_id=input.target_user_id,
                message=f"{user['username']} swapped credit multipliers with you for 1 hour! ({user_multiplier:.1f}x ↔ {target_multiplier:.1f}x)",
                notification_type="inversion_used",
                related_user_id=input.user_id
            )
            await db.notifications.insert_one(notification.dict())
        
        elif "trade_request" in item["effect"]:
            # Trade Pass - create a trade request requiring mutual consent
            # For now, create a simple credit swap request (could be enhanced later)
            user_credits = user.get("credits", 0) - item["price"]  # Credits after purchase
            target_credits = target_user.get("credits", 0)
            
            # Create trade request (proposing equal credit swap for simplicity)
            trade_amount = min(user_credits, target_credits) // 2  # Propose swapping half of lesser amount
            if trade_amount < 10:  # Minimum 10 FC trade
                trade_amount = 10
                
            trade_request = TradeRequest(
                requester_id=input.user_id,
                target_id=input.target_user_id,
                requester_credits=trade_amount,
                target_credits=trade_amount
            )
            await db.trade_requests.insert_one(trade_request.dict())
            
            # Create notification for target
            notification = Notification(
                user_id=input.target_user_id,
                message=f"{user['username']} wants to trade {trade_amount} FC with you! Check your trade requests.",
                notification_type="trade_request",
                related_user_id=input.user_id
            )
            await db.notifications.insert_one(notification.dict())
            
            # Deduct credits from requester
            await db.users.update_one(
                {"id": input.user_id},
                {"$inc": {"credits": -item["price"]}}
            )
            
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

# ==================== WEEKLY PLANNER ENDPOINTS ====================

@api_router.post("/weekly-tasks", response_model=WeeklyTask)
async def create_weekly_task(input: WeeklyTaskCreate):
    # Get current week start (Monday)
    now = datetime.utcnow()
    days_since_monday = now.weekday()
    week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    task = WeeklyTask(
        **input.dict(),
        week_start=week_start
    )
    await db.weekly_tasks.insert_one(task.dict())
    return task

@api_router.get("/weekly-tasks/{user_id}", response_model=List[WeeklyTask])
async def get_user_weekly_tasks(user_id: str, week_offset: int = 0):
    # Calculate week start based on offset (0 = current week, -1 = previous week, etc.)
    now = datetime.utcnow()
    days_since_monday = now.weekday()
    current_week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = current_week_start + timedelta(weeks=week_offset)
    week_end = week_start + timedelta(days=7)
    
    tasks = await db.weekly_tasks.find({
        "user_id": user_id,
        "week_start": {"$gte": week_start, "$lt": week_end}
    }).to_list(1000)
    
    return [WeeklyTask(**task) for task in tasks]

@api_router.post("/weekly-tasks/complete", response_model=Dict[str, Any])
async def complete_weekly_task(input: WeeklyTaskComplete):
    # Get user and task
    user = await db.users.find_one({"id": input.user_id})
    task = await db.weekly_tasks.find_one({"id": input.task_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not task:
        raise HTTPException(status_code=404, detail="Weekly task not found")
    
    # Check if task belongs to user
    if task["user_id"] != input.user_id:
        raise HTTPException(status_code=403, detail="You can only complete your own tasks")
    
    # Check if task is already completed
    if task.get("is_completed", False):
        raise HTTPException(status_code=400, detail="Task is already completed")
    
    # Mark task as completed
    await db.weekly_tasks.update_one(
        {"id": input.task_id},
        {
            "$set": {
                "is_completed": True,
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    # Award credits (10 FC for weekly tasks)
    credits_earned = 10
    await db.users.update_one(
        {"id": input.user_id},
        {
            "$inc": {
                "credits": credits_earned,
                "completed_tasks": 1
            }
        }
    )
    
    return {
        "success": True,
        "credits_earned": credits_earned,
        "task_title": task["title"],
        "total_credits": user["credits"] + credits_earned
    }

@api_router.delete("/weekly-tasks/{task_id}")
async def delete_weekly_task(task_id: str, user_id: str):
    # Check if task exists and belongs to user
    task = await db.weekly_tasks.find_one({"id": task_id, "user_id": user_id})
    if not task:
        raise HTTPException(status_code=404, detail="Weekly task not found")
    
    await db.weekly_tasks.delete_one({"id": task_id})
    return {"success": True}

# ==================== TRADE REQUEST ENDPOINTS ====================

@api_router.get("/trade-requests/{user_id}", response_model=List[TradeRequest])
async def get_user_trade_requests(user_id: str):
    """Get pending trade requests for a user (both sent and received)"""
    # Clean expired requests first
    await db.trade_requests.delete_many({
        "expires_at": {"$lt": datetime.utcnow().isoformat()},
        "status": "pending"
    })
    
    requests = await db.trade_requests.find({
        "$or": [
            {"requester_id": user_id},
            {"target_id": user_id}
        ],
        "status": "pending"
    }).sort("created_at", -1).to_list(50)
    
    return [TradeRequest(**req) for req in requests]

@api_router.post("/trade-requests/respond", response_model=Dict[str, Any])
async def respond_to_trade_request(input: TradeResponse):
    """Accept or reject a trade request"""
    # Get trade request
    trade_request = await db.trade_requests.find_one({
        "id": input.trade_request_id,
        "status": "pending"
    })
    
    if not trade_request:
        raise HTTPException(status_code=404, detail="Trade request not found or already processed")
    
    # Check if request has expired
    if datetime.fromisoformat(trade_request["expires_at"]) < datetime.utcnow():
        await db.trade_requests.update_one(
            {"id": input.trade_request_id},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=400, detail="Trade request has expired")
    
    # Get both users
    requester = await db.users.find_one({"id": trade_request["requester_id"]})
    target = await db.users.find_one({"id": trade_request["target_id"]})
    
    if not requester or not target:
        raise HTTPException(status_code=404, detail="One or both users not found")
    
    if input.response == "accept":
        # Check if both users have enough credits
        requester_credits = requester.get("credits", 0)
        target_credits = target.get("credits", 0)
        
        if requester_credits < trade_request["requester_credits"]:
            raise HTTPException(status_code=400, detail="Requester doesn't have enough credits")
        if target_credits < trade_request["target_credits"]:
            raise HTTPException(status_code=400, detail="You don't have enough credits")
        
        # Execute the trade
        await db.users.update_one(
            {"id": trade_request["requester_id"]},
            {"$inc": {"credits": trade_request["target_credits"] - trade_request["requester_credits"]}}
        )
        await db.users.update_one(
            {"id": trade_request["target_id"]},
            {"$inc": {"credits": trade_request["requester_credits"] - trade_request["target_credits"]}}
        )
        
        # Update trade request status
        await db.trade_requests.update_one(
            {"id": input.trade_request_id},
            {"$set": {"status": "accepted"}}
        )
        
        # Notify both users
        requester_notification = Notification(
            user_id=trade_request["requester_id"],
            message=f"Trade completed! You exchanged {trade_request['requester_credits']} FC for {trade_request['target_credits']} FC with {target['username']}",
            notification_type="trade_completed",
            related_user_id=trade_request["target_id"]
        )
        target_notification = Notification(
            user_id=trade_request["target_id"],
            message=f"Trade completed! You exchanged {trade_request['target_credits']} FC for {trade_request['requester_credits']} FC with {requester['username']}",
            notification_type="trade_completed",
            related_user_id=trade_request["requester_id"]
        )
        
        await db.notifications.insert_one(requester_notification.dict())
        await db.notifications.insert_one(target_notification.dict())
        
        return {
            "success": True,
            "message": "Trade completed successfully!",
            "status": "accepted"
        }
    
    else:  # reject
        # Update trade request status
        await db.trade_requests.update_one(
            {"id": input.trade_request_id},
            {"$set": {"status": "rejected"}}
        )
        
        # Notify requester
        notification = Notification(
            user_id=trade_request["requester_id"],
            message=f"{target['username']} declined your trade request",
            notification_type="trade_rejected",
            related_user_id=trade_request["target_id"]
        )
        await db.notifications.insert_one(notification.dict())
        
        return {
            "success": True,
            "message": "Trade request rejected",
            "status": "rejected"
        }

# ==================== STUDY STATISTICS ENDPOINTS ====================

@api_router.get("/statistics/{user_id}", response_model=Dict[str, Any])
async def get_user_statistics(user_id: str):
    # Get user data
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Focus sessions data for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    focus_sessions = await db.focus_sessions.find({
        "user_id": user_id,
        "end_time": {"$gte": thirty_days_ago},
        "is_active": False
    }).sort("end_time", 1).to_list(1000)
    
    # Process daily focus time
    daily_focus = {}
    daily_credits = {}
    for session in focus_sessions:
        date_key = session["end_time"].strftime("%Y-%m-%d")
        daily_focus[date_key] = daily_focus.get(date_key, 0) + session.get("duration_minutes", 0)
        daily_credits[date_key] = daily_credits.get(date_key, 0) + session.get("credits_earned", 0)
    
    # Task completion data
    regular_tasks_completed = await db.tasks.count_documents({
        "user_id": user_id, 
        "is_completed": True
    })
    
    weekly_tasks_completed = await db.weekly_tasks.count_documents({
        "user_id": user_id, 
        "is_completed": True
    })
    
    # Level progression (simplified - could be enhanced with level history)
    current_level = user.get("level", 1)
    
    # Weekly breakdown for last 4 weeks
    weekly_data = []
    for week_offset in range(-3, 1):  # Last 4 weeks including current
        week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday() + (3 - week_offset) * 7)
        week_end = week_start + timedelta(days=7)
        
        week_sessions = [s for s in focus_sessions 
                        if week_start <= s["end_time"] < week_end]
        
        week_focus_time = sum(s.get("duration_minutes", 0) for s in week_sessions)
        week_credits = sum(s.get("credits_earned", 0) for s in week_sessions)
        
        weekly_data.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "focus_minutes": week_focus_time,
            "credits_earned": week_credits,
            "sessions_count": len(week_sessions)
        })
    
    return {
        "user_stats": {
            "total_focus_time": user.get("total_focus_time", 0),
            "total_credits": user.get("credits", 0),
            "current_level": current_level,
            "credit_rate": user.get("credit_rate_multiplier", 1.0),
            "regular_tasks_completed": regular_tasks_completed,
            "weekly_tasks_completed": weekly_tasks_completed,
            "total_tasks_completed": regular_tasks_completed + weekly_tasks_completed
        },
        "daily_focus_time": daily_focus,
        "daily_credits": daily_credits,
        "weekly_breakdown": weekly_data,
        "recent_sessions_count": len(focus_sessions)
    }

# ==================== WHEEL ENDPOINTS ====================

@api_router.get("/wheel/status/{user_id}", response_model=Dict[str, Any])
async def get_wheel_status(user_id: str):
    """Check if user can spin the wheel today and get their level"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is level 6 or higher
    if user.get("level", 1) < 6:
        return {
            "can_spin": False,
            "reason": "requires_level_6",
            "user_level": user.get("level", 1),
            "required_level": 6
        }
    
    # Check if user has already spun today
    last_spin = user.get("last_wheel_spin")
    if last_spin:
        # Convert string to datetime if needed
        if isinstance(last_spin, str):
            last_spin = datetime.fromisoformat(last_spin.replace('Z', '+00:00'))
        
        # Check if it's the same day
        today = datetime.utcnow().date()
        last_spin_date = last_spin.date()
        
        if last_spin_date == today:
            return {
                "can_spin": False,
                "reason": "already_spun_today",
                "last_spin": last_spin.isoformat(),
                "next_spin_available": (datetime.combine(today + timedelta(days=1), datetime.min.time())).isoformat()
            }
    
    return {
        "can_spin": True,
        "user_level": user.get("level", 1)
    }

@api_router.post("/wheel/spin", response_model=Dict[str, Any])
async def spin_wheel(input: Dict[str, str]):
    """Spin the daily wheel for FC rewards (10-100 FC)"""
    user_id = input.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is level 6 or higher
    if user.get("level", 1) < 6:
        raise HTTPException(status_code=403, detail="Wheel unlocks at level 6")
    
    # Check if user has already spun today
    last_spin = user.get("last_wheel_spin")
    if last_spin:
        # Convert string to datetime if needed
        if isinstance(last_spin, str):
            last_spin = datetime.fromisoformat(last_spin.replace('Z', '+00:00'))
        
        # Check if it's the same day
        today = datetime.utcnow().date()
        last_spin_date = last_spin.date()
        
        if last_spin_date == today:
            raise HTTPException(status_code=400, detail="You can only spin the wheel once per day")
    
    # Generate random reward (10-100 FC)
    import random
    reward = random.randint(10, 100)
    
    # Update user credits and last spin time
    current_time = datetime.utcnow()
    await db.users.update_one(
        {"id": user_id},
        {
            "$inc": {"credits": reward},
            "$set": {"last_wheel_spin": current_time}
        }
    )
    
    # Create notification for wheel spin
    notification = Notification(
        user_id=user_id,
        message=f"🎰 Daily wheel spin earned you {reward} FC!",
        notification_type="wheel_reward",
        timestamp=current_time
    )
    await db.notifications.insert_one(notification.dict())
    
    return {
        "success": True,
        "reward": reward,
        "message": f"Congratulations! You won {reward} FC!",
        "next_spin_available": (datetime.combine(current_time.date() + timedelta(days=1), datetime.min.time())).isoformat()
    }

# ==================== ADMIN/UTILITY ENDPOINTS ====================

@api_router.post("/admin/reset-database")
async def reset_database():
    """Reset database - remove all users, sessions, purchases, notifications, tasks, weekly tasks"""
    await db.users.delete_many({})
    await db.focus_sessions.delete_many({})
    await db.purchases.delete_many({})
    await db.notifications.delete_many({})
    await db.tasks.delete_many({})
    await db.weekly_tasks.delete_many({})
    return {"message": "Database reset successfully"}

@api_router.post("/init")
async def initialize_shop_items():
    """Initialize shop with new pass system"""
    
    try:
        # Reset shop items
        delete_result = await db.shop_items.delete_many({})
        print(f"Deleted {delete_result.deleted_count} existing shop items")
        
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
                "description": "Select someone → their credit rate is halved for 24 hours",
                "emoji": "💀",
                "price": 120,
                "item_type": "sabotage",
                "effect": {"rate_halved": True},
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
            },
            # NEW ADVANCED PASSES
            {
                "id": str(uuid.uuid4()),
                "name": "Mirror Pass",
                "description": "Reflects the next pass used against you back to the original sender",
                "emoji": "🪞",
                "price": 250,
                "item_type": "defensive",
                "effect": {"mirror_shield": True},
                "is_active": True,
                "requires_target": False,
                "duration_hours": 24
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Dominance Pass",
                "description": "For 1 hour, all other players earn only 50% of their usual credits",
                "emoji": "👑",
                "price": 300,
                "item_type": "sabotage",
                "effect": {"global_dominance": True},
                "is_active": True,
                "requires_target": False,
                "duration_hours": 1
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Time Loop Pass",
                "description": "Instantly repeats your last hour's credit gain. Highly effective after group focus sessions",
                "emoji": "⏰",
                "price": 200,
                "item_type": "boost",
                "effect": {"time_loop": True},
                "is_active": True,
                "requires_target": False
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Immunity Pass",
                "description": "Grants complete immunity from all negative passes for 48 hours",
                "emoji": "🛡️",
                "price": 300,
                "item_type": "defensive",
                "effect": {"immunity_shield": True},
                "is_active": True,
                "requires_target": False,
                "duration_hours": 48
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Assassin Pass",
                "description": "Targeted player earns 0 credits for their next 3 tasks",
                "emoji": "🗡️",
                "price": 120,
                "item_type": "sabotage",
                "effect": {"assassin_curse": True, "tasks_affected": 3},
                "is_active": True,
                "requires_target": True,
                "duration_hours": 24
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Freeze Pass",
                "description": "Prevents the targeted player from using any passes for the next 12 hours",
                "emoji": "🧊",
                "price": 150,
                "item_type": "sabotage",
                "effect": {"freeze_passes": True},
                "is_active": True,
                "requires_target": True,
                "duration_hours": 12
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Inversion Pass",
                "description": "Swaps your credit rate multiplier with another player for 60 minutes",
                "emoji": "🔀",
                "price": 180,
                "item_type": "special",
                "effect": {"inversion_swap": True},
                "is_active": True,
                "requires_target": True,
                "duration_hours": 1
            }
        ]
        
        print(f"Attempting to insert {len(new_items)} shop items")
        insert_result = await db.shop_items.insert_many(new_items)
        print(f"Successfully inserted {len(insert_result.inserted_ids)} shop items")
        
        return {"message": f"Shop items initialized successfully - {len(insert_result.inserted_ids)} items added"}
    
    except Exception as e:
        print(f"Error initializing shop items: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize shop items: {str(e)}")

@api_router.post("/add-advanced-passes")
async def add_advanced_passes():
    """Add the 7 advanced passes to existing shop"""
    
    try:
        # Check existing passes
        existing_count = await db.shop_items.count_documents({})
        print(f"Found {existing_count} existing shop items")
        
        # Check if advanced passes already exist
        mirror_exists = await db.shop_items.count_documents({"name": "Mirror Pass"})
        if mirror_exists > 0:
            return {"message": "Advanced passes already exist", "total_items": existing_count}
        
        advanced_passes = [
            {
                "id": str(uuid.uuid4()),
                "name": "Mirror Pass",
                "description": "Reflects the next pass used against you back to the original sender",
                "emoji": "🪞",
                "price": 250,
                "item_type": "defensive",
                "effect": {"mirror_shield": True},
                "is_active": True,
                "requires_target": False,
                "duration_hours": 24
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Dominance Pass",
                "description": "For 1 hour, all other players earn only 50% of their usual credits",
                "emoji": "👑",
                "price": 300,
                "item_type": "sabotage",
                "effect": {"global_dominance": True},
                "is_active": True,
                "requires_target": False,
                "duration_hours": 1
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Time Loop Pass",
                "description": "Instantly repeats your last hour's credit gain. Highly effective after group focus sessions",
                "emoji": "⏰",
                "price": 200,
                "item_type": "boost",
                "effect": {"time_loop": True},
                "is_active": True,
                "requires_target": False
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Immunity Pass",
                "description": "Grants complete immunity from all negative passes for 48 hours",
                "emoji": "🛡️",
                "price": 300,
                "item_type": "defensive",
                "effect": {"immunity_shield": True},
                "is_active": True,
                "requires_target": False,
                "duration_hours": 48
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Assassin Pass",
                "description": "Targeted player earns 0 credits for their next 3 tasks",
                "emoji": "🗡️",
                "price": 120,
                "item_type": "sabotage",
                "effect": {"assassin_curse": True, "tasks_affected": 3},
                "is_active": True,
                "requires_target": True,
                "duration_hours": 24
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Freeze Pass",
                "description": "Prevents the targeted player from using any passes for the next 12 hours",
                "emoji": "🧊",
                "price": 150,
                "item_type": "sabotage",
                "effect": {"freeze_passes": True},
                "is_active": True,
                "requires_target": True,
                "duration_hours": 12
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Inversion Pass",
                "description": "Swaps your credit rate multiplier with another player for 60 minutes",
                "emoji": "🔀",
                "price": 180,
                "item_type": "special",
                "effect": {"inversion_swap": True},
                "is_active": True,
                "requires_target": True,
                "duration_hours": 1
            }
        ]
        
        print(f"Adding {len(advanced_passes)} advanced passes")
        insert_result = await db.shop_items.insert_many(advanced_passes)
        
        final_count = await db.shop_items.count_documents({})
        print(f"Successfully added {len(insert_result.inserted_ids)} advanced passes. Total items: {final_count}")
        
        return {"message": f"Added {len(insert_result.inserted_ids)} advanced passes successfully", "total_items": final_count}
    
    except Exception as e:
        print(f"Error adding advanced passes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add advanced passes: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# Health check endpoint (without /api prefix for Railway health checks)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {"message": "Focus Royale Backend is running!", "status": "ok"}

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

@app.on_event("startup")
async def startup_db_client():
    """Initialize database on startup if needed"""
    try:
        # Check if shop_items collection is empty
        shop_count = await db.shop_items.count_documents({})
        
        if shop_count == 0:
            logger.info("Shop items collection is empty. Initializing with all passes...")
            
            # Initialize with all pass data (same as /init endpoint)
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
                    "description": "Select someone → their credit rate is halved for 24 hours",
                    "emoji": "💀",
                    "price": 120,
                    "item_type": "sabotage",
                    "effect": {"rate_halved": True},
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
                },
                # NEW ADVANCED PASSES
                {
                    "id": str(uuid.uuid4()),
                    "name": "Mirror Pass",
                    "description": "Reflects the next pass used against you back to the original sender",
                    "emoji": "🪞",
                    "price": 250,
                    "item_type": "defensive",
                    "effect": {"mirror_shield": True},
                    "is_active": True,
                    "requires_target": False,
                    "duration_hours": 24
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Dominance Pass",
                    "description": "For 1 hour, all other players earn only 50% of their usual credits",
                    "emoji": "👑",
                    "price": 300,
                    "item_type": "sabotage",
                    "effect": {"global_dominance": True},
                    "is_active": True,
                    "requires_target": False,
                    "duration_hours": 1
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Time Loop Pass",
                    "description": "Instantly repeats your last hour's credit gain. Highly effective after group focus sessions",
                    "emoji": "⏰",
                    "price": 200,
                    "item_type": "boost",
                    "effect": {"time_loop": True},
                    "is_active": True,
                    "requires_target": False
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Immunity Pass",
                    "description": "Grants complete immunity from all negative passes for 48 hours",
                    "emoji": "🛡️",
                    "price": 300,
                    "item_type": "defensive",
                    "effect": {"immunity_shield": True},
                    "is_active": True,
                    "requires_target": False,
                    "duration_hours": 48
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Assassin Pass",
                    "description": "Targeted player earns 0 credits for their next 3 tasks",
                    "emoji": "🗡️",
                    "price": 120,
                    "item_type": "sabotage",
                    "effect": {"assassin_curse": True, "tasks_affected": 3},
                    "is_active": True,
                    "requires_target": True,
                    "duration_hours": 24
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Freeze Pass",
                    "description": "Prevents the targeted player from using any passes for the next 12 hours",
                    "emoji": "🧊",
                    "price": 150,
                    "item_type": "sabotage",
                    "effect": {"freeze_passes": True},
                    "is_active": True,
                    "requires_target": True,
                    "duration_hours": 12
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Inversion Pass",
                    "description": "Swaps your credit rate multiplier with another player for 60 minutes",
                    "emoji": "🔀",
                    "price": 180,
                    "item_type": "special",
                    "effect": {"inversion_swap": True},
                    "is_active": True,
                    "requires_target": True,
                    "duration_hours": 1
                }
            ]
            
            await db.shop_items.insert_many(new_items)
            logger.info(f"Successfully initialized {len(new_items)} shop items on startup")
        else:
            logger.info(f"Shop items already exist ({shop_count} items). Skipping initialization.")
            
    except Exception as e:
        logger.error(f"Error during startup initialization: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Railway deployment configuration
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)