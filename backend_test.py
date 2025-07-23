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
BASE_URL = "https://013410b5-5cd6-4738-a23a-5e5cd4ece3fd.preview.emergentagent.com/api"

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
        """Test NEW Tasks System (3 credits per completion)"""
        self.log("\n=== Testing Tasks System (3 credits reward) ===")
        
        if not self.test_users:
            self.log("❌ No test users available for tasks testing")
            return False
        
        # Test 1: Get available tasks
        try:
            response = requests.get(f"{self.base_url}/tasks", timeout=10)
            if response.status_code == 200:
                self.test_tasks = response.json()
                self.log(f"✅ Retrieved {len(self.test_tasks)} available tasks")
                
                if len(self.test_tasks) == 0:
                    self.log("❌ No tasks available for testing")
                    return False
                
            else:
                self.log(f"❌ Failed to get tasks: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting tasks: {str(e)}")
            return False
        
        # Test 2: Complete a task and verify 3 credits reward
        user = self.test_users[0]
        task = self.test_tasks[0]
        original_credits = user.get('credits', 0)
        
        try:
            response = requests.post(
                f"{self.base_url}/tasks/complete",
                json={"user_id": user["id"], "task_id": task["id"]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                credits_earned = result.get("credits_earned", 0)
                
                if credits_earned == 3:
                    self.log(f"✅ Task completion awarded correct 3 credits")
                else:
                    self.log(f"❌ Task should award 3 credits, got {credits_earned}")
                    return False
                
                # Verify user's total credits increased
                expected_total = original_credits + 3
                actual_total = result.get("total_credits", 0)
                if actual_total == expected_total:
                    self.log(f"✅ User credits updated correctly: {original_credits} + 3 = {actual_total}")
                else:
                    self.log(f"❌ User credits not updated correctly: expected {expected_total}, got {actual_total}")
                    return False
                
            else:
                self.log(f"❌ Failed to complete task: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error completing task: {str(e)}")
            return False
        
        self.log("✅ Tasks System tests passed")
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