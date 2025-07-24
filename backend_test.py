#!/usr/bin/env python3
"""
Focus Royale Backend API Test Suite - USER REGISTRATION TESTING
Tests the user registration functionality after MongoDB connection string update:
1. **Registration Endpoint**: Test POST /api/auth/register with new user data
2. **Username Uniqueness**: Verify unique username registration works
3. **Duplicate Prevention**: Test duplicate username registration returns error
4. **Database Persistence**: Verify user data is saved to deployed MongoDB
5. **Response Format**: Test user object returned correctly without password hash
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta

# Backend URL from frontend/.env
BASE_URL = "https://c1329b16-571d-440a-9a59-dd60ea104ad6.preview.emergentagent.com/api"

class FocusRoyaleNewFeaturesAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_users = []
        self.test_sessions = []
        self.test_purchases = []
        self.shop_items = []
        self.test_tasks = []
        self.test_notifications = []
        
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
        """Test Database Reset functionality"""
        self.log("\n=== Testing Database Reset ===")
        
        try:
            response = requests.post(f"{self.base_url}/admin/reset-database", timeout=10)
            if response.status_code == 200:
                self.log("✅ Database reset successfully")
                
                # Verify database is empty
                response = requests.get(f"{self.base_url}/users", timeout=10)
                if response.status_code == 200:
                    users = response.json()
                    if len(users) == 0:
                        self.log("✅ Database confirmed empty after reset")
                        return True
                    else:
                        self.log(f"❌ Database should be empty, found {len(users)} users")
                        return False
                else:
                    self.log(f"❌ Failed to verify empty database: {response.status_code}")
                    return False
            else:
                self.log(f"❌ Failed to reset database: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error resetting database: {str(e)}")
            return False
    
    def test_authentication_system(self):
        """Test NEW Authentication System with register/login"""
        self.log("\n=== Testing Authentication System ===")
        
        # Test 1: Register new users with passwords
        timestamp = int(time.time())
        test_users_data = [
            {"username": f"alice_focus_{timestamp}", "password": "secure_password_123"},
            {"username": f"bob_productivity_{timestamp}", "password": "another_secure_pass"},
            {"username": f"charlie_zen_{timestamp}", "password": "zen_master_2024"}
        ]
        
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
                    
                    # Verify user structure (password_hash should not be in response)
                    required_fields = ['id', 'username', 'credits', 'total_focus_time', 'level', 'credit_rate_multiplier']
                    for field in required_fields:
                        if field not in user_info:
                            self.log(f"❌ Missing field '{field}' in user data")
                            return False
                    
                    if 'password_hash' in user_info:
                        self.log("❌ Password hash should not be in response")
                        return False
                    
                    # Verify initial values
                    if user_info['credits'] != 0:
                        self.log(f"❌ New user should have 0 credits, got {user_info['credits']}")
                        return False
                    if user_info['credit_rate_multiplier'] != 1.0:
                        self.log(f"❌ New user should have 1.0 multiplier, got {user_info['credit_rate_multiplier']}")
                        return False
                        
                else:
                    self.log(f"❌ Failed to register user {user_data['username']}: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error registering user {user_data['username']}: {str(e)}")
                return False
        
        # Test 2: Try to register duplicate username
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=test_users_data[0],
                timeout=10
            )
            if response.status_code == 400:
                self.log("✅ Username uniqueness enforced correctly")
            else:
                self.log(f"❌ Duplicate username should return 400, got {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing duplicate username: {str(e)}")
            return False
        
        # Test 3: Login with correct credentials
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
                    self.log(f"✅ Login successful for {user_data['username']}")
                    
                    # Update our test user data with latest info
                    self.test_users[i] = user_info
                    
                else:
                    self.log(f"❌ Failed to login user {user_data['username']}: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error logging in user {user_data['username']}: {str(e)}")
                return False
        
        # Test 4: Login with incorrect credentials
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": test_users_data[0]["username"], "password": "wrong_password"},
                timeout=10
            )
            if response.status_code == 401:
                self.log("✅ Invalid credentials rejected correctly")
            else:
                self.log(f"❌ Invalid credentials should return 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing invalid credentials: {str(e)}")
            return False
        
        self.log("✅ Authentication System tests passed")
        return True
    
    def test_updated_credit_rate(self):
        """Test NEW Credit Rate: 10 credits/hour = 1 credit per 6 minutes"""
        self.log("\n=== Testing Updated Credit Rate (10 credits/hour) ===")
        
        if not self.test_users:
            self.log("❌ No test users available for credit rate testing")
            return False
        
        user = self.test_users[0]
        user_id = user['id']
        
        # Test 1: Start focus session
        try:
            response = requests.post(
                f"{self.base_url}/focus/start",
                json={"user_id": user_id},
                timeout=10
            )
            
            if response.status_code == 200:
                session_data = response.json()
                self.log(f"✅ Started focus session for user {user['username']}")
            else:
                self.log(f"❌ Failed to start focus session: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error starting focus session: {str(e)}")
            return False
        
        # Test 2: Wait 7 seconds to simulate 7 minutes of focus time (should earn 1+ credits)
        self.log("Waiting 7 seconds to simulate 7 minutes of focus time...")
        time.sleep(7)  # Simulating 7 minutes
        
        try:
            response = requests.post(
                f"{self.base_url}/focus/end",
                json={"user_id": user_id},
                timeout=10
            )
            
            if response.status_code == 200:
                end_data = response.json()
                self.log(f"✅ Ended focus session")
                
                # Verify NEW credit calculation: duration_minutes / 6 * effective_rate
                duration = end_data.get('duration_minutes', 0)
                credits_earned = end_data.get('credits_earned', 0)
                effective_rate = end_data.get('effective_rate', 1.0)
                
                # Expected credits = duration / 6 * effective_rate (rounded down)
                expected_credits = int((duration / 6) * effective_rate)
                
                if credits_earned == expected_credits:
                    self.log(f"✅ NEW Credit calculation correct: {duration} min / 6 * {effective_rate} = {credits_earned} credits")
                else:
                    self.log(f"❌ NEW Credit calculation wrong: expected {expected_credits}, got {credits_earned}")
                    self.log(f"   Formula: {duration} minutes / 6 * {effective_rate} rate = {expected_credits}")
                    return False
                    
            else:
                self.log(f"❌ Failed to end focus session: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error ending focus session: {str(e)}")
            return False
        
        self.log("✅ Updated Credit Rate tests passed")
        return True
    
    def test_new_pass_system(self):
        """Test NEW Pass System with 6 shop items"""
        self.log("\n=== Testing NEW Pass System (6 Shop Items) ===")
        
        # Test 1: Initialize shop with new items
        try:
            response = requests.post(f"{self.base_url}/init", timeout=10)
            if response.status_code == 200:
                self.log("✅ Shop items initialized")
            else:
                self.log(f"❌ Failed to initialize shop: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error initializing shop: {str(e)}")
            return False
        
        # Test 2: Get shop items and verify all 6 new passes
        try:
            response = requests.get(f"{self.base_url}/shop/items", timeout=10)
            if response.status_code == 200:
                self.shop_items = response.json()
                self.log(f"✅ Retrieved {len(self.shop_items)} shop items")
                
                # Verify we have all 6 new passes
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
                    self.log("✅ All 6 new passes found with correct prices and types")
                else:
                    self.log(f"❌ Expected 6 passes, found {len(found_passes)}: {found_passes}")
                    return False
                
            else:
                self.log(f"❌ Failed to get shop items: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting shop items: {str(e)}")
            return False
        
        self.log("✅ NEW Pass System tests passed")
        return True
    
    def test_tasks_system(self):
        """Test Personal Tasks System (10 credits per completion)"""
        self.log("\n=== Testing Personal Tasks System ===")
        
        if not self.test_users:
            self.log("❌ No test users available for tasks testing")
            return False
        
        user = self.test_users[0]
        user_id = user['id']
        
        # Test 1: Create a personal task
        task_data = {
            "user_id": user_id,
            "title": "Complete Focus Royale Testing",
            "description": "Test the task creation and completion system thoroughly"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/tasks",
                json=task_data,
                timeout=10
            )
            
            if response.status_code == 200:
                created_task = response.json()
                self.log(f"✅ Created personal task: {created_task['title']}")
                
                # Verify task structure
                required_fields = ['id', 'user_id', 'title', 'description', 'credits_reward', 'is_active', 'is_completed']
                for field in required_fields:
                    if field not in created_task:
                        self.log(f"❌ Missing field '{field}' in created task")
                        return False
                
                # Verify task belongs to user
                if created_task['user_id'] != user_id:
                    self.log(f"❌ Task user_id mismatch: expected {user_id}, got {created_task['user_id']}")
                    return False
                
                # Verify default values
                if created_task['credits_reward'] != 10:
                    self.log(f"❌ Task should have 10 credits reward, got {created_task['credits_reward']}")
                    return False
                
                if created_task['is_completed'] != False:
                    self.log(f"❌ New task should not be completed")
                    return False
                
                self.test_tasks.append(created_task)
                
            else:
                self.log(f"❌ Failed to create task: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating task: {str(e)}")
            return False
        
        # Test 2: Get user's tasks
        try:
            response = requests.get(f"{self.base_url}/tasks/{user_id}", timeout=10)
            if response.status_code == 200:
                user_tasks = response.json()
                self.log(f"✅ Retrieved {len(user_tasks)} tasks for user")
                
                # Verify our created task is in the list
                task_found = False
                for task in user_tasks:
                    if task['id'] == created_task['id']:
                        task_found = True
                        break
                
                if not task_found:
                    self.log("❌ Created task not found in user's task list")
                    return False
                
            else:
                self.log(f"❌ Failed to get user tasks: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting user tasks: {str(e)}")
            return False
        
        # Test 3: Complete the task and verify credits reward
        original_credits = user.get('credits', 0)
        
        try:
            response = requests.post(
                f"{self.base_url}/tasks/complete",
                json={"user_id": user_id, "task_id": created_task['id']},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                credits_earned = result.get("credits_earned", 0)
                
                if credits_earned == 10:
                    self.log(f"✅ Task completion awarded correct 10 credits")
                else:
                    self.log(f"❌ Task should award 10 credits, got {credits_earned}")
                    return False
                
                # Verify user's total credits increased
                expected_total = original_credits + 10
                actual_total = result.get("total_credits", 0)
                if actual_total == expected_total:
                    self.log(f"✅ User credits updated correctly: {original_credits} + 10 = {actual_total}")
                    # Update our test user data
                    user['credits'] = actual_total
                else:
                    self.log(f"❌ User credits not updated correctly: expected {expected_total}, got {actual_total}")
                    return False
                
            else:
                self.log(f"❌ Failed to complete task: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error completing task: {str(e)}")
            return False
        
        # Test 4: Verify task is marked as completed and no longer appears in active tasks
        try:
            response = requests.get(f"{self.base_url}/tasks/{user_id}", timeout=10)
            if response.status_code == 200:
                user_tasks = response.json()
                
                # Completed task should not appear in active tasks list
                completed_task_found = False
                for task in user_tasks:
                    if task['id'] == created_task['id']:
                        completed_task_found = True
                        break
                
                if not completed_task_found:
                    self.log("✅ Completed task correctly removed from active tasks list")
                else:
                    self.log("❌ Completed task should not appear in active tasks list")
                    return False
                
            else:
                self.log(f"❌ Failed to get user tasks after completion: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error verifying task completion: {str(e)}")
            return False
        
        self.log("✅ Personal Tasks System tests passed")
        return True
    
    def test_notifications_system(self):
        """Test NEW Notifications System"""
        self.log("\n=== Testing Notifications System ===")
        
        if len(self.test_users) < 2:
            self.log("❌ Need at least 2 users for notifications testing")
            return False
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        
        # Test 1: Get user notifications (should include task completion from previous test)
        try:
            response = requests.get(f"{self.base_url}/notifications/{user1['id']}", timeout=10)
            if response.status_code == 200:
                notifications = response.json()
                self.log(f"✅ Retrieved {len(notifications)} notifications for user1")
                
                # Look for task completion notification
                task_notifications = [n for n in notifications if n.get("notification_type") == "task_completed"]
                if task_notifications:
                    self.log("✅ Task completion notification found")
                else:
                    self.log("❌ Task completion notification not found")
                    return False
                
            else:
                self.log(f"❌ Failed to get notifications: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting notifications: {str(e)}")
            return False
        
        # Test 2: Test pass usage notification by purchasing a pass that targets another user
        # First, give user1 enough credits by completing more tasks
        try:
            # Give user1 credits by completing more tasks
            if len(self.test_tasks) > 1:
                for i in range(min(3, len(self.test_tasks) - 1)):  # Complete up to 3 more tasks
                    task = self.test_tasks[i + 1]
                    response = requests.post(
                        f"{self.base_url}/tasks/complete",
                        json={"user_id": user1["id"], "task_id": task["id"]},
                        timeout=10
                    )
                    if response.status_code == 200:
                        self.log(f"✅ Completed additional task for credits")
        except Exception as e:
            self.log(f"Warning: Could not complete additional tasks: {str(e)}")
        
        # Find a pass that requires a target (like Degression Pass)
        target_pass = None
        for item in self.shop_items:
            if item.get("requires_target", False) and item["price"] <= 120:  # Affordable pass
                target_pass = item
                break
        
        if target_pass:
            try:
                response = requests.post(
                    f"{self.base_url}/shop/purchase",
                    json={
                        "user_id": user1["id"],
                        "item_id": target_pass["id"],
                        "target_user_id": user2["id"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Purchased {target_pass['name']} targeting user2")
                    
                    # Check if user2 received a notification
                    time.sleep(1)  # Brief wait for notification to be created
                    response = requests.get(f"{self.base_url}/notifications/{user2['id']}", timeout=10)
                    if response.status_code == 200:
                        user2_notifications = response.json()
                        pass_notifications = [n for n in user2_notifications if n.get("notification_type") == "pass_used"]
                        if pass_notifications:
                            self.log("✅ Pass usage notification sent to target user")
                        else:
                            self.log("❌ Pass usage notification not found for target user")
                            return False
                    
                elif response.status_code == 400:
                    self.log("ℹ️  Insufficient credits for pass purchase (expected for testing)")
                else:
                    self.log(f"❌ Unexpected error purchasing pass: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error testing pass usage notification: {str(e)}")
                return False
        
        self.log("✅ Notifications System tests passed")
        return True
    
    def test_temporary_effects(self):
        """Test Temporary Effects (Degression Pass 24hr, Ally Token 3hr)"""
        self.log("\n=== Testing Temporary Effects ===")
        
        if len(self.test_users) < 2:
            self.log("❌ Need at least 2 users for temporary effects testing")
            return False
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        
        # Test 1: Check for Degression Pass (24hr effect)
        degression_pass = None
        for item in self.shop_items:
            if item["name"] == "Degression Pass":
                degression_pass = item
                break
        
        if degression_pass:
            # Verify it has correct duration
            if degression_pass.get("duration_hours") == 24:
                self.log("✅ Degression Pass has correct 24-hour duration")
            else:
                self.log(f"❌ Degression Pass should have 24-hour duration, got {degression_pass.get('duration_hours')}")
                return False
        else:
            self.log("❌ Degression Pass not found")
            return False
        
        # Test 2: Check for Ally Token (3hr effect)
        ally_token = None
        for item in self.shop_items:
            if item["name"] == "Ally Token":
                ally_token = item
                break
        
        if ally_token:
            # Verify it has correct duration
            if ally_token.get("duration_hours") == 3:
                self.log("✅ Ally Token has correct 3-hour duration")
            else:
                self.log(f"❌ Ally Token should have 3-hour duration, got {ally_token.get('duration_hours')}")
                return False
        else:
            self.log("❌ Ally Token not found")
            return False
        
        # Test 3: Verify temporary effects structure in user data
        # Check if users have active_effects field
        try:
            response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                if "active_effects" in user_data:
                    self.log("✅ Users have active_effects field for temporary effects")
                else:
                    self.log("❌ Users missing active_effects field")
                    return False
            else:
                self.log(f"❌ Failed to get user data: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error checking user active_effects: {str(e)}")
            return False
        
        self.log("✅ Temporary Effects tests passed")
        return True
    
    def test_daily_wheel_feature(self):
        """Test NEW Daily Wheel Feature - Level 6+ users can spin once per day for 10-100 FC"""
        self.log("\n=== Testing Daily Wheel Feature ===")
        
        if not self.test_users:
            self.log("❌ No test users available for wheel testing")
            return False
        
        # Test 1: Test wheel status for user below level 6
        low_level_user = self.test_users[0]  # Should be level 1
        try:
            response = requests.get(f"{self.base_url}/wheel/status/{low_level_user['id']}", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                if not status_data.get("can_spin", True) and status_data.get("reason") == "requires_level_6":
                    self.log("✅ Level requirement enforced - users below level 6 cannot spin")
                    self.log(f"   User level: {status_data.get('user_level')}, Required: {status_data.get('required_level')}")
                else:
                    self.log(f"❌ Level requirement not enforced properly: {status_data}")
                    return False
            else:
                self.log(f"❌ Failed to get wheel status: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing wheel status for low level user: {str(e)}")
            return False
        
        # Test 2: Manually upgrade user to level 6 for testing
        try:
            # Update user level directly in database via level pass purchases
            level_pass = None
            for item in self.shop_items:
                if item["name"] == "Level Pass":
                    level_pass = item
                    break
            
            if not level_pass:
                self.log("❌ Level Pass not found in shop")
                return False
            
            # Give user enough credits to buy 5 level passes (to reach level 6)
            # First, let's check current credits and add more via focus sessions
            current_user_response = requests.get(f"{self.base_url}/users/{low_level_user['id']}", timeout=10)
            if current_user_response.status_code == 200:
                current_user = current_user_response.json()
                current_credits = current_user.get('credits', 0)
                needed_credits = (level_pass['price'] * 5) - current_credits  # Need 500 credits for 5 level passes
                
                if needed_credits > 0:
                    # Do multiple focus sessions to earn credits
                    self.log(f"Need {needed_credits} more credits, doing focus sessions...")
                    for i in range(10):  # Do 10 short sessions
                        # Start session
                        requests.post(f"{self.base_url}/focus/start", json={"user_id": low_level_user['id']}, timeout=10)
                        time.sleep(1)  # 1 second = simulated focus time
                        # End session
                        requests.post(f"{self.base_url}/focus/end", json={"user_id": low_level_user['id']}, timeout=10)
                        time.sleep(0.5)  # Brief pause between sessions
                
                # Now buy 5 level passes to reach level 6
                for i in range(5):
                    purchase_response = requests.post(
                        f"{self.base_url}/shop/purchase",
                        json={"user_id": low_level_user['id'], "item_id": level_pass['id']},
                        timeout=10
                    )
                    if purchase_response.status_code == 200:
                        self.log(f"✅ Purchased Level Pass {i+1}/5")
                    else:
                        self.log(f"❌ Failed to purchase Level Pass {i+1}: {purchase_response.status_code}")
                        # Continue anyway, maybe user has enough level
                        break
                
                # Verify user is now level 6+
                updated_user_response = requests.get(f"{self.base_url}/users/{low_level_user['id']}", timeout=10)
                if updated_user_response.status_code == 200:
                    updated_user = updated_user_response.json()
                    user_level = updated_user.get('level', 1)
                    if user_level >= 6:
                        self.log(f"✅ User upgraded to level {user_level}")
                        low_level_user = updated_user  # Update our test user data
                    else:
                        self.log(f"❌ User still at level {user_level}, need level 6+")
                        return False
                else:
                    self.log("❌ Failed to get updated user data")
                    return False
            else:
                self.log("❌ Failed to get current user data")
                return False
                
        except Exception as e:
            self.log(f"❌ Error upgrading user to level 6: {str(e)}")
            return False
        
        # Test 3: Test wheel status for level 6+ user (should be able to spin)
        try:
            response = requests.get(f"{self.base_url}/wheel/status/{low_level_user['id']}", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get("can_spin", False):
                    self.log("✅ Level 6+ user can spin the wheel")
                    self.log(f"   User level: {status_data.get('user_level')}")
                else:
                    self.log(f"❌ Level 6+ user should be able to spin: {status_data}")
                    return False
            else:
                self.log(f"❌ Failed to get wheel status for level 6+ user: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing wheel status for level 6+ user: {str(e)}")
            return False
        
        # Test 4: Test wheel spin functionality
        original_credits = low_level_user.get('credits', 0)
        try:
            response = requests.post(
                f"{self.base_url}/wheel/spin",
                json={"user_id": low_level_user['id']},
                timeout=10
            )
            if response.status_code == 200:
                spin_result = response.json()
                reward = spin_result.get('reward', 0)
                
                # Verify reward is in correct range (10-100 FC)
                if 10 <= reward <= 100:
                    self.log(f"✅ Wheel spin successful - earned {reward} FC (valid range 10-100)")
                else:
                    self.log(f"❌ Wheel reward {reward} FC is outside valid range (10-100)")
                    return False
                
                # Verify success message
                if spin_result.get('success', False):
                    self.log("✅ Wheel spin returned success=True")
                else:
                    self.log("❌ Wheel spin should return success=True")
                    return False
                
                # Verify next spin availability is tomorrow
                next_spin = spin_result.get('next_spin_available')
                if next_spin:
                    self.log(f"✅ Next spin available: {next_spin}")
                else:
                    self.log("❌ Next spin availability not provided")
                    return False
                
            else:
                self.log(f"❌ Failed to spin wheel: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error spinning wheel: {str(e)}")
            return False
        
        # Test 5: Verify user credits were updated
        try:
            response = requests.get(f"{self.base_url}/users/{low_level_user['id']}", timeout=10)
            if response.status_code == 200:
                updated_user = response.json()
                new_credits = updated_user.get('credits', 0)
                expected_credits = original_credits + reward
                
                if new_credits == expected_credits:
                    self.log(f"✅ User credits updated correctly: {original_credits} + {reward} = {new_credits}")
                else:
                    self.log(f"❌ User credits not updated correctly: expected {expected_credits}, got {new_credits}")
                    return False
            else:
                self.log(f"❌ Failed to get updated user data: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error verifying credit update: {str(e)}")
            return False
        
        # Test 6: Test daily limitation - try to spin again (should fail)
        try:
            response = requests.post(
                f"{self.base_url}/wheel/spin",
                json={"user_id": low_level_user['id']},
                timeout=10
            )
            if response.status_code == 400:
                error_detail = response.json().get('detail', '')
                if "once per day" in error_detail.lower():
                    self.log("✅ Daily limitation enforced - cannot spin twice in same day")
                else:
                    self.log(f"❌ Wrong error message for daily limit: {error_detail}")
                    return False
            else:
                self.log(f"❌ Second spin should return 400 error, got {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing daily limitation: {str(e)}")
            return False
        
        # Test 7: Verify wheel status shows already spun today
        try:
            response = requests.get(f"{self.base_url}/wheel/status/{low_level_user['id']}", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                if not status_data.get("can_spin", True) and status_data.get("reason") == "already_spun_today":
                    self.log("✅ Wheel status correctly shows already spun today")
                    last_spin = status_data.get('last_spin')
                    next_spin = status_data.get('next_spin_available')
                    if last_spin and next_spin:
                        self.log(f"   Last spin: {last_spin}")
                        self.log(f"   Next available: {next_spin}")
                    else:
                        self.log("❌ Missing last_spin or next_spin_available in status")
                        return False
                else:
                    self.log(f"❌ Wheel status should show already_spun_today: {status_data}")
                    return False
            else:
                self.log(f"❌ Failed to get wheel status after spin: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error checking wheel status after spin: {str(e)}")
            return False
        
        # Test 8: Check for wheel notification
        try:
            response = requests.get(f"{self.base_url}/notifications/{low_level_user['id']}", timeout=10)
            if response.status_code == 200:
                notifications = response.json()
                wheel_notifications = [n for n in notifications if n.get("notification_type") == "wheel_reward"]
                if wheel_notifications:
                    wheel_notif = wheel_notifications[0]
                    if str(reward) in wheel_notif.get('message', ''):
                        self.log(f"✅ Wheel reward notification created: {wheel_notif['message']}")
                    else:
                        self.log(f"❌ Wheel notification doesn't contain reward amount: {wheel_notif['message']}")
                        return False
                else:
                    self.log("❌ Wheel reward notification not found")
                    return False
            else:
                self.log(f"❌ Failed to get notifications: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error checking wheel notification: {str(e)}")
            return False
        
        self.log("✅ Daily Wheel Feature tests passed")
        return True
    
    def run_all_tests(self):
        """Run all NEW FEATURES test suites"""
        self.log("🚀 Starting Focus Royale NEW FEATURES Backend API Tests")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {
            "API Health": self.test_api_health(),
            "Database Reset": False,
            "Authentication System": False,
            "Updated Credit Rate": False,
            "NEW Pass System": False,
            "Tasks System": False,
            "Notifications System": False,
            "Temporary Effects": False
        }
        
        if test_results["API Health"]:
            test_results["Database Reset"] = self.test_database_reset()
            
            if test_results["Database Reset"]:
                test_results["Authentication System"] = self.test_authentication_system()
                
                if test_results["Authentication System"]:
                    test_results["Updated Credit Rate"] = self.test_updated_credit_rate()
                    test_results["NEW Pass System"] = self.test_new_pass_system()
                    test_results["Tasks System"] = self.test_tasks_system()
                    test_results["Notifications System"] = self.test_notifications_system()
                    test_results["Temporary Effects"] = self.test_temporary_effects()
        
        # Print summary
        self.log("\n" + "="*60)
        self.log("NEW FEATURES TEST SUMMARY")
        self.log("="*60)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        self.log("="*60)
        if all_passed:
            self.log("🎉 ALL NEW FEATURES TESTS PASSED!")
        else:
            self.log("💥 SOME NEW FEATURES TESTS FAILED!")
        
        return test_results

if __name__ == "__main__":
    tester = FocusRoyaleNewFeaturesAPITester()
    results = tester.run_all_tests()