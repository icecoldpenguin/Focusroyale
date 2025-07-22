#!/usr/bin/env python3
"""
Focus Royale Backend API Test Suite - PERSONAL TASK SYSTEM & SHOP PASSES
Tests the new personal task creation system and comprehensive shop pass functionality:
- Personal Task Creation System (user-specific tasks)
- Task Ownership and Completion (3 credits reward)
- Shop Pass System (Level, Progression, Degression, Reset, Ally, Trade)
- Targeting System and Credit Deduction
- Temporary Effects and Rate Calculations
- Activity Notifications and User Workflow
- Authentication System (register/login)
- Leaderboard (registered users only)
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta

# Backend URL from frontend/.env
BASE_URL = "https://d06fa30a-3a94-4fec-bca1-1b5cfcbea68c.preview.emergentagent.com/api"

class PersonalTaskShopTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_users = []
        self.test_tasks = []
        self.shop_items = []
        self.test_purchases = []
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def test_api_health(self):
        """Test if the API is accessible"""
        self.log("Testing API health...")
        try:
            response = requests.get(f"{self.base_url}/users", timeout=10)
            if response.status_code in [200, 404]:  # 404 is ok if no users exist yet
                self.log("✅ API is accessible")
                return True
            else:
                self.log(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ API health check failed: {str(e)}")
            return False
    
    def test_database_reset(self):
        """Reset database for clean testing"""
        self.log("\n=== Resetting Database for Clean Testing ===")
        
        try:
            response = requests.post(f"{self.base_url}/admin/reset-database", timeout=10)
            if response.status_code == 200:
                self.log("✅ Database reset successfully")
                
                # Initialize shop items
                response = requests.post(f"{self.base_url}/init", timeout=10)
                if response.status_code == 200:
                    self.log("✅ Shop items initialized")
                    return True
                else:
                    self.log(f"❌ Failed to initialize shop: {response.status_code}")
                    return False
            else:
                self.log(f"❌ Failed to reset database: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error resetting database: {str(e)}")
            return False
    
    def test_user_registration_and_login(self):
        """Test user registration and login system"""
        self.log("\n=== Testing User Registration and Login ===")
        
        # Create test users with realistic data
        timestamp = int(time.time())
        test_users_data = [
            {"username": f"sarah_focus_{timestamp}", "password": "secure_pass_2024"},
            {"username": f"mike_productivity_{timestamp}", "password": "strong_password_123"},
            {"username": f"emma_zen_{timestamp}", "password": "mindful_focus_pass"}
        ]
        
        # Test 1: Register users
        for user_data in test_users_data:
            try:
                response = requests.post(
                    f"{self.base_url}/auth/register",
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    user_info = result.get("user", {})
                    self.test_users.append(user_info)
                    self.log(f"✅ Registered user: {user_data['username']} (ID: {user_info['id']})")
                    
                    # Verify initial user state
                    if user_info['credits'] != 0:
                        self.log(f"❌ New user should have 0 credits, got {user_info['credits']}")
                        return False
                    if user_info['credit_rate_multiplier'] != 1.0:
                        self.log(f"❌ New user should have 1.0 multiplier, got {user_info['credit_rate_multiplier']}")
                        return False
                        
                else:
                    self.log(f"❌ Failed to register user {user_data['username']}: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error registering user {user_data['username']}: {str(e)}")
                return False
        
        # Test 2: Login with correct credentials
        for i, user_data in enumerate(test_users_data):
            try:
                response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={"username": user_data["username"], "password": user_data["password"]},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    user_info = result.get("user", {})
                    self.test_users[i] = user_info  # Update with latest data
                    self.log(f"✅ Login successful for {user_data['username']}")
                else:
                    self.log(f"❌ Failed to login user {user_data['username']}: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error logging in user {user_data['username']}: {str(e)}")
                return False
        
        self.log("✅ User registration and login tests passed")
        return True
    
    def test_personal_task_creation(self):
        """Test creating personal tasks via POST /api/tasks with user_id, title, description"""
        self.log("\n=== Testing Personal Task Creation ===")
        
        if not self.test_users:
            self.log("❌ No test users available")
            return False
        
        user = self.test_users[0]
        
        # Test 1: Create personal tasks for user
        task_data_list = [
            {
                "user_id": user["id"],
                "title": "Complete morning workout routine",
                "description": "30 minutes of cardio and strength training to start the day right"
            },
            {
                "user_id": user["id"],
                "title": "Review quarterly project goals",
                "description": "Analyze progress on Q4 objectives and plan next steps"
            },
            {
                "user_id": user["id"],
                "title": "Learn new programming concept",
                "description": "Study async/await patterns in Python for 45 minutes"
            }
        ]
        
        for task_data in task_data_list:
            try:
                response = requests.post(
                    f"{self.base_url}/tasks",
                    json=task_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    task = response.json()
                    self.test_tasks.append(task)
                    self.log(f"✅ Created task: '{task['title']}'")
                    
                    # Verify task structure
                    if task['user_id'] != user["id"]:
                        self.log(f"❌ Task user_id mismatch: expected {user['id']}, got {task['user_id']}")
                        return False
                    if task['credits_reward'] != 3:
                        self.log(f"❌ Task should reward 3 credits, got {task['credits_reward']}")
                        return False
                    if task['is_completed'] != False:
                        self.log(f"❌ New task should not be completed")
                        return False
                        
                else:
                    self.log(f"❌ Failed to create task: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error creating task: {str(e)}")
                return False
        
        # Test 2: Create tasks for second user
        if len(self.test_users) > 1:
            user2 = self.test_users[1]
            task_data = {
                "user_id": user2["id"],
                "title": "Organize digital workspace",
                "description": "Clean up desktop files and organize project folders"
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/tasks",
                    json=task_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    task = response.json()
                    self.test_tasks.append(task)
                    self.log(f"✅ Created task for user2: '{task['title']}'")
                else:
                    self.log(f"❌ Failed to create task for user2: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error creating task for user2: {str(e)}")
                return False
        
        self.log("✅ Personal task creation tests passed")
        return True
    
    def test_user_specific_task_retrieval(self):
        """Test fetching user's personal tasks via GET /api/tasks/{user_id} - should only return that user's incomplete tasks"""
        self.log("\n=== Testing User-Specific Task Retrieval ===")
        
        if not self.test_users or not self.test_tasks:
            self.log("❌ No test users or tasks available")
            return False
        
        user1 = self.test_users[0]
        
        # Test 1: Get user1's tasks
        try:
            response = requests.get(f"{self.base_url}/tasks/{user1['id']}", timeout=10)
            
            if response.status_code == 200:
                user_tasks = response.json()
                self.log(f"✅ Retrieved {len(user_tasks)} tasks for user1")
                
                # Verify all tasks belong to user1
                for task in user_tasks:
                    if task['user_id'] != user1['id']:
                        self.log(f"❌ Found task belonging to different user: {task['user_id']}")
                        return False
                    if task['is_completed'] == True:
                        self.log(f"❌ Found completed task in active list: {task['title']}")
                        return False
                
                # Verify we got the expected number of tasks for user1 (3 tasks created)
                expected_user1_tasks = len([t for t in self.test_tasks if t['user_id'] == user1['id']])
                if len(user_tasks) != expected_user1_tasks:
                    self.log(f"❌ Expected {expected_user1_tasks} tasks for user1, got {len(user_tasks)}")
                    return False
                
                self.log("✅ User1 tasks correctly filtered by ownership and completion status")
                
            else:
                self.log(f"❌ Failed to get user1 tasks: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting user1 tasks: {str(e)}")
            return False
        
        # Test 2: Get user2's tasks (if exists)
        if len(self.test_users) > 1:
            user2 = self.test_users[1]
            try:
                response = requests.get(f"{self.base_url}/tasks/{user2['id']}", timeout=10)
                
                if response.status_code == 200:
                    user2_tasks = response.json()
                    self.log(f"✅ Retrieved {len(user2_tasks)} tasks for user2")
                    
                    # Verify all tasks belong to user2
                    for task in user2_tasks:
                        if task['user_id'] != user2['id']:
                            self.log(f"❌ Found task belonging to different user in user2's list")
                            return False
                    
                    # Verify user2 has different tasks than user1
                    expected_user2_tasks = len([t for t in self.test_tasks if t['user_id'] == user2['id']])
                    if len(user2_tasks) != expected_user2_tasks:
                        self.log(f"❌ Expected {expected_user2_tasks} tasks for user2, got {len(user2_tasks)}")
                        return False
                    
                    self.log("✅ User2 tasks correctly isolated from user1")
                    
                else:
                    self.log(f"❌ Failed to get user2 tasks: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error getting user2 tasks: {str(e)}")
                return False
        
        self.log("✅ User-specific task retrieval tests passed")
        return True
    
    def test_task_completion_and_ownership(self):
        """Test task completion via POST /api/tasks/complete - should mark task as completed, award 3 credits, update user stats, and create activity notification"""
        self.log("\n=== Testing Task Completion and Ownership ===")
        
        if not self.test_users or not self.test_tasks:
            self.log("❌ No test users or tasks available")
            return False
        
        user1 = self.test_users[0]
        user1_task = None
        
        # Find a task belonging to user1
        for task in self.test_tasks:
            if task['user_id'] == user1['id']:
                user1_task = task
                break
        
        if not user1_task:
            self.log("❌ No task found for user1")
            return False
        
        # Get user1's current credits
        try:
            response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
            if response.status_code == 200:
                user_before = response.json()
                original_credits = user_before['credits']
                original_completed_tasks = user_before.get('completed_tasks', 0)
            else:
                self.log(f"❌ Failed to get user data before completion: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting user data before completion: {str(e)}")
            return False
        
        # Test 1: Complete user1's own task
        try:
            response = requests.post(
                f"{self.base_url}/tasks/complete",
                json={"user_id": user1["id"], "task_id": user1_task["id"]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Successfully completed task: '{user1_task['title']}'")
                
                # Verify credits awarded
                credits_earned = result.get("credits_earned", 0)
                if credits_earned != 3:
                    self.log(f"❌ Should award 3 credits, got {credits_earned}")
                    return False
                
                # Verify total credits calculation
                expected_total = original_credits + 3
                actual_total = result.get("total_credits", 0)
                if actual_total != expected_total:
                    self.log(f"❌ Total credits mismatch: expected {expected_total}, got {actual_total}")
                    return False
                
                self.log(f"✅ Awarded 3 credits correctly: {original_credits} + 3 = {actual_total}")
                
            else:
                self.log(f"❌ Failed to complete task: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error completing task: {str(e)}")
            return False
        
        # Test 2: Verify user stats updated
        try:
            response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
            if response.status_code == 200:
                user_after = response.json()
                
                # Check credits updated
                if user_after['credits'] != original_credits + 3:
                    self.log(f"❌ User credits not updated: expected {original_credits + 3}, got {user_after['credits']}")
                    return False
                
                # Check completed tasks counter
                if user_after.get('completed_tasks', 0) != original_completed_tasks + 1:
                    self.log(f"❌ Completed tasks counter not updated: expected {original_completed_tasks + 1}, got {user_after.get('completed_tasks', 0)}")
                    return False
                
                self.log("✅ User stats updated correctly")
                
            else:
                self.log(f"❌ Failed to get updated user data: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting updated user data: {str(e)}")
            return False
        
        # Test 3: Verify task marked as completed and doesn't appear in active list
        try:
            response = requests.get(f"{self.base_url}/tasks/{user1['id']}", timeout=10)
            if response.status_code == 200:
                active_tasks = response.json()
                
                # Completed task should not appear in active list
                for task in active_tasks:
                    if task['id'] == user1_task['id']:
                        self.log(f"❌ Completed task still appears in active list")
                        return False
                
                self.log("✅ Completed task correctly removed from active list")
                
            else:
                self.log(f"❌ Failed to get active tasks: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting active tasks: {str(e)}")
            return False
        
        # Test 4: Verify activity notification created
        try:
            response = requests.get(f"{self.base_url}/notifications/{user1['id']}", timeout=10)
            if response.status_code == 200:
                notifications = response.json()
                
                # Look for task completion notification
                task_notifications = [n for n in notifications if n.get("notification_type") == "task_completed"]
                if task_notifications:
                    self.log("✅ Task completion notification created")
                else:
                    self.log("❌ Task completion notification not found")
                    return False
                
            else:
                self.log(f"❌ Failed to get notifications: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting notifications: {str(e)}")
            return False
        
        # Test 5: Verify task ownership - users can only complete their own tasks
        if len(self.test_users) > 1 and len(self.test_tasks) > 1:
            user2 = self.test_users[1]
            
            # Try to complete user1's task as user2 (should fail)
            user1_other_task = None
            for task in self.test_tasks:
                if task['user_id'] == user1['id'] and task['id'] != user1_task['id']:
                    user1_other_task = task
                    break
            
            if user1_other_task:
                try:
                    response = requests.post(
                        f"{self.base_url}/tasks/complete",
                        json={"user_id": user2["id"], "task_id": user1_other_task["id"]},
                        timeout=10
                    )
                    
                    if response.status_code == 403:
                        self.log("✅ Task ownership validation working - user2 cannot complete user1's task")
                    else:
                        self.log(f"❌ Task ownership validation failed: expected 403, got {response.status_code}")
                        return False
                        
                except Exception as e:
                    self.log(f"❌ Error testing task ownership: {str(e)}")
                    return False
        
        # Test 6: Try to complete already completed task (should fail)
        try:
            response = requests.post(
                f"{self.base_url}/tasks/complete",
                json={"user_id": user1["id"], "task_id": user1_task["id"]},
                timeout=10
            )
            
            if response.status_code == 400:
                self.log("✅ Cannot complete already completed task")
            else:
                self.log(f"❌ Should prevent completing already completed task: got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing double completion: {str(e)}")
            return False
        
        self.log("✅ Task completion and ownership tests passed")
        return True
    
    def test_shop_pass_system(self):
        """Test all shop pass types work correctly"""
        self.log("\n=== Testing Shop Pass System ===")
        
        # Get shop items
        try:
            response = requests.get(f"{self.base_url}/shop/items", timeout=10)
            if response.status_code == 200:
                self.shop_items = response.json()
                self.log(f"✅ Retrieved {len(self.shop_items)} shop items")
                
                # Verify we have all 6 expected passes
                expected_passes = [
                    {"name": "Level Pass", "price": 100, "type": "level"},
                    {"name": "Progression Pass", "price": 80, "type": "boost"},
                    {"name": "Degression Pass", "price": 120, "type": "sabotage"},
                    {"name": "Reset Pass", "price": 500, "type": "sabotage"},
                    {"name": "Ally Token", "price": 60, "type": "special"},
                    {"name": "Trade Pass", "price": 50, "type": "special"}
                ]
                
                found_passes = []
                for item in self.shop_items:
                    for expected in expected_passes:
                        if item["name"] == expected["name"]:
                            found_passes.append(expected["name"])
                            if item["price"] != expected["price"]:
                                self.log(f"❌ {expected['name']} has wrong price: expected {expected['price']}, got {item['price']}")
                                return False
                            if item["item_type"] != expected["type"]:
                                self.log(f"❌ {expected['name']} has wrong type: expected {expected['type']}, got {item['item_type']}")
                                return False
                
                if len(found_passes) == 6:
                    self.log("✅ All 6 shop passes found with correct prices and types")
                else:
                    self.log(f"❌ Expected 6 passes, found {len(found_passes)}: {found_passes}")
                    return False
                
            else:
                self.log(f"❌ Failed to get shop items: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting shop items: {str(e)}")
            return False
        
        self.log("✅ Shop pass system tests passed")
        return True
    
    def test_shop_pass_functionality(self):
        """Test shop pass purchases and effects"""
        self.log("\n=== Testing Shop Pass Functionality ===")
        
        if len(self.test_users) < 2:
            self.log("❌ Need at least 2 users for pass testing")
            return False
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        
        # Give user1 enough credits by completing more tasks
        self.log("Giving user1 more credits by completing tasks...")
        user1_tasks = [t for t in self.test_tasks if t['user_id'] == user1['id'] and t['id'] != self.test_tasks[0]['id']]
        
        for task in user1_tasks[:2]:  # Complete 2 more tasks (6 more credits)
            try:
                response = requests.post(
                    f"{self.base_url}/tasks/complete",
                    json={"user_id": user1["id"], "task_id": task["id"]},
                    timeout=10
                )
                if response.status_code == 200:
                    self.log(f"✅ Completed task for credits: '{task['title']}'")
            except Exception as e:
                self.log(f"Warning: Could not complete task: {str(e)}")
        
        # Get updated user1 data
        try:
            response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
            if response.status_code == 200:
                user1 = response.json()
                self.log(f"User1 now has {user1['credits']} credits")
            else:
                self.log(f"❌ Failed to get updated user1 data: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting updated user1 data: {str(e)}")
            return False
        
        # Test 1: Level Pass (increases user level by 1)
        level_pass = None
        for item in self.shop_items:
            if item["name"] == "Level Pass":
                level_pass = item
                break
        
        if level_pass and user1['credits'] >= level_pass['price']:
            try:
                original_level = user1['level']
                original_credits = user1['credits']
                
                response = requests.post(
                    f"{self.base_url}/shop/purchase",
                    json={
                        "user_id": user1["id"],
                        "item_id": level_pass["id"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ Purchased Level Pass")
                    
                    # Verify user level increased
                    response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
                    if response.status_code == 200:
                        updated_user = response.json()
                        if updated_user['level'] == original_level + 1:
                            self.log("✅ Level Pass correctly increased user level by 1")
                        else:
                            self.log(f"❌ Level Pass failed: expected level {original_level + 1}, got {updated_user['level']}")
                            return False
                        
                        if updated_user['credits'] == original_credits - level_pass['price']:
                            self.log("✅ Level Pass correctly deducted credits")
                        else:
                            self.log(f"❌ Level Pass credit deduction failed: expected {original_credits - level_pass['price']}, got {updated_user['credits']}")
                            return False
                        
                        user1 = updated_user  # Update for next tests
                    else:
                        self.log(f"❌ Failed to get updated user after Level Pass: {response.status_code}")
                        return False
                        
                else:
                    self.log(f"❌ Failed to purchase Level Pass: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error testing Level Pass: {str(e)}")
                return False
        else:
            self.log("ℹ️  Skipping Level Pass test - insufficient credits or pass not found")
        
        # Test 2: Progression Pass (increases credit rate multiplier by +0.5x permanently)
        progression_pass = None
        for item in self.shop_items:
            if item["name"] == "Progression Pass":
                progression_pass = item
                break
        
        if progression_pass and user1['credits'] >= progression_pass['price']:
            try:
                original_multiplier = user1['credit_rate_multiplier']
                original_credits = user1['credits']
                
                response = requests.post(
                    f"{self.base_url}/shop/purchase",
                    json={
                        "user_id": user1["id"],
                        "item_id": progression_pass["id"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Purchased Progression Pass")
                    
                    # Verify multiplier increased
                    response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
                    if response.status_code == 200:
                        updated_user = response.json()
                        expected_multiplier = original_multiplier + 0.5
                        if abs(updated_user['credit_rate_multiplier'] - expected_multiplier) < 0.01:
                            self.log(f"✅ Progression Pass correctly increased multiplier to {updated_user['credit_rate_multiplier']}")
                        else:
                            self.log(f"❌ Progression Pass failed: expected multiplier {expected_multiplier}, got {updated_user['credit_rate_multiplier']}")
                            return False
                        
                        user1 = updated_user  # Update for next tests
                    else:
                        self.log(f"❌ Failed to get updated user after Progression Pass: {response.status_code}")
                        return False
                        
                else:
                    self.log(f"❌ Failed to purchase Progression Pass: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error testing Progression Pass: {str(e)}")
                return False
        else:
            self.log("ℹ️  Skipping Progression Pass test - insufficient credits or pass not found")
        
        # Test 3: Targeting system - Degression Pass (requires target user)
        degression_pass = None
        for item in self.shop_items:
            if item["name"] == "Degression Pass":
                degression_pass = item
                break
        
        if degression_pass and user1['credits'] >= degression_pass['price']:
            try:
                response = requests.post(
                    f"{self.base_url}/shop/purchase",
                    json={
                        "user_id": user1["id"],
                        "item_id": degression_pass["id"],
                        "target_user_id": user2["id"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Purchased Degression Pass targeting user2")
                    
                    # Verify target user has active effect
                    response = requests.get(f"{self.base_url}/users/{user2['id']}", timeout=10)
                    if response.status_code == 200:
                        target_user = response.json()
                        active_effects = target_user.get('active_effects', [])
                        
                        degression_effects = [e for e in active_effects if e.get('type') == 'degression']
                        if degression_effects:
                            self.log("✅ Degression Pass correctly applied temporary effect to target")
                        else:
                            self.log("❌ Degression Pass did not apply effect to target")
                            return False
                    else:
                        self.log(f"❌ Failed to get target user after Degression Pass: {response.status_code}")
                        return False
                        
                else:
                    self.log(f"❌ Failed to purchase Degression Pass: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error testing Degression Pass: {str(e)}")
                return False
        else:
            self.log("ℹ️  Skipping Degression Pass test - insufficient credits or pass not found")
        
        # Test 4: Test targeting validation - pass without target should fail
        if degression_pass:
            try:
                response = requests.post(
                    f"{self.base_url}/shop/purchase",
                    json={
                        "user_id": user1["id"],
                        "item_id": degression_pass["id"]
                        # No target_user_id provided
                    },
                    timeout=10
                )
                
                if response.status_code == 400:
                    self.log("✅ Targeting validation working - pass requiring target fails without target")
                else:
                    self.log(f"❌ Targeting validation failed: expected 400, got {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error testing targeting validation: {str(e)}")
                return False
        
        self.log("✅ Shop pass functionality tests passed")
        return True
    
    def test_leaderboard_registered_users_only(self):
        """Test that only registered users appear in leaderboard (no example users)"""
        self.log("\n=== Testing Leaderboard (Registered Users Only) ===")
        
        try:
            response = requests.get(f"{self.base_url}/leaderboard", timeout=10)
            if response.status_code == 200:
                leaderboard = response.json()
                self.log(f"✅ Retrieved leaderboard with {len(leaderboard)} users")
                
                # Verify all users in leaderboard are our registered test users
                test_user_ids = [user['id'] for user in self.test_users]
                
                for user in leaderboard:
                    if user['id'] not in test_user_ids:
                        # Check if it's an example user (should not exist)
                        if 'alice_focus' in user['username'] or 'bob_productivity' in user['username']:
                            if not any(test_user['username'] == user['username'] for test_user in self.test_users):
                                self.log(f"❌ Found example user in leaderboard: {user['username']}")
                                return False
                
                # Verify leaderboard is sorted by credits (descending)
                for i in range(len(leaderboard) - 1):
                    if leaderboard[i]['credits'] < leaderboard[i + 1]['credits']:
                        self.log(f"❌ Leaderboard not sorted correctly by credits")
                        return False
                
                self.log("✅ Leaderboard contains only registered users and is sorted correctly")
                
            else:
                self.log(f"❌ Failed to get leaderboard: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting leaderboard: {str(e)}")
            return False
        
        self.log("✅ Leaderboard tests passed")
        return True
    
    def test_complete_user_workflow(self):
        """Test complete user workflow: register → create tasks → complete tasks → earn credits → buy passes → use passes on other users"""
        self.log("\n=== Testing Complete User Workflow ===")
        
        # This test combines all the previous functionality in a realistic workflow
        # Most of the workflow has already been tested in previous methods
        
        # Verify we have users with credits from task completion
        if not self.test_users:
            self.log("❌ No test users for workflow test")
            return False
        
        user1 = self.test_users[0]
        
        # Get final user state
        try:
            response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
            if response.status_code == 200:
                final_user = response.json()
                
                # Verify user has earned credits from task completion
                if final_user['credits'] > 0:
                    self.log(f"✅ User workflow complete - user has {final_user['credits']} credits from task completion")
                else:
                    self.log("❌ User should have earned credits from task completion")
                    return False
                
                # Verify user has completed tasks
                if final_user.get('completed_tasks', 0) > 0:
                    self.log(f"✅ User has completed {final_user['completed_tasks']} tasks")
                else:
                    self.log("❌ User should have completed tasks counter > 0")
                    return False
                
                # Verify user level may have increased from Level Pass
                if final_user['level'] > 1:
                    self.log(f"✅ User level increased to {final_user['level']} from pass purchase")
                
                # Verify user multiplier may have increased from Progression Pass
                if final_user['credit_rate_multiplier'] > 1.0:
                    self.log(f"✅ User multiplier increased to {final_user['credit_rate_multiplier']} from pass purchase")
                
            else:
                self.log(f"❌ Failed to get final user state: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting final user state: {str(e)}")
            return False
        
        # Verify activity notifications exist
        try:
            response = requests.get(f"{self.base_url}/notifications/{user1['id']}", timeout=10)
            if response.status_code == 200:
                notifications = response.json()
                
                # Should have task completion notifications
                task_notifications = [n for n in notifications if n.get("notification_type") == "task_completed"]
                if task_notifications:
                    self.log(f"✅ Found {len(task_notifications)} task completion notifications")
                else:
                    self.log("❌ No task completion notifications found")
                    return False
                
                # May have purchase notifications
                purchase_notifications = [n for n in notifications if n.get("notification_type") == "purchase"]
                if purchase_notifications:
                    self.log(f"✅ Found {len(purchase_notifications)} purchase notifications")
                
            else:
                self.log(f"❌ Failed to get notifications: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting notifications: {str(e)}")
            return False
        
        self.log("✅ Complete user workflow tests passed")
        return True
    
    def run_all_tests(self):
        """Run all personal task system and shop pass tests"""
        self.log("🚀 Starting Personal Task System & Shop Pass Tests")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {
            "API Health": self.test_api_health(),
            "Database Reset": False,
            "User Registration & Login": False,
            "Personal Task Creation": False,
            "User-Specific Task Retrieval": False,
            "Task Completion & Ownership": False,
            "Shop Pass System": False,
            "Shop Pass Functionality": False,
            "Leaderboard (Registered Users Only)": False,
            "Complete User Workflow": False
        }
        
        if test_results["API Health"]:
            test_results["Database Reset"] = self.test_database_reset()
            
            if test_results["Database Reset"]:
                test_results["User Registration & Login"] = self.test_user_registration_and_login()
                
                if test_results["User Registration & Login"]:
                    test_results["Personal Task Creation"] = self.test_personal_task_creation()
                    
                    if test_results["Personal Task Creation"]:
                        test_results["User-Specific Task Retrieval"] = self.test_user_specific_task_retrieval()
                        test_results["Task Completion & Ownership"] = self.test_task_completion_and_ownership()
                        test_results["Shop Pass System"] = self.test_shop_pass_system()
                        
                        if test_results["Task Completion & Ownership"] and test_results["Shop Pass System"]:
                            test_results["Shop Pass Functionality"] = self.test_shop_pass_functionality()
                            test_results["Leaderboard (Registered Users Only)"] = self.test_leaderboard_registered_users_only()
                            test_results["Complete User Workflow"] = self.test_complete_user_workflow()
        
        # Print summary
        self.log("\n" + "="*70)
        self.log("PERSONAL TASK SYSTEM & SHOP PASS TEST SUMMARY")
        self.log("="*70)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        self.log("="*70)
        if all_passed:
            self.log("🎉 ALL PERSONAL TASK SYSTEM & SHOP PASS TESTS PASSED!")
        else:
            self.log("💥 SOME TESTS FAILED!")
        
        return test_results

if __name__ == "__main__":
    tester = PersonalTaskShopTester()
    results = tester.run_all_tests()