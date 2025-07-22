#!/usr/bin/env python3
"""
Focus Royale Backend API Test Suite
Tests all backend endpoints and critical business logic
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://ca5de1e9-00d4-4aad-a316-ec592a1b2530.preview.emergentagent.com/api"

class FocusRoyaleAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_users = []
        self.test_sessions = []
        self.test_purchases = []
        self.shop_items = []
        
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
    
    def test_user_management(self):
        """Test User Management System"""
        self.log("\n=== Testing User Management System ===")
        
        # Test 1: Create users with unique usernames
        test_usernames = ["alice_focus", "bob_productivity", "charlie_zen"]
        
        for username in test_usernames:
            try:
                response = requests.post(
                    f"{self.base_url}/users",
                    json={"username": username},
                    timeout=10
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.test_users.append(user_data)
                    self.log(f"✅ Created user: {username} (ID: {user_data['id']})")
                    
                    # Verify user structure
                    required_fields = ['id', 'username', 'credits', 'total_focus_time', 'level', 'credit_rate_multiplier']
                    for field in required_fields:
                        if field not in user_data:
                            self.log(f"❌ Missing field '{field}' in user data")
                            return False
                    
                    # Verify initial values
                    if user_data['credits'] != 0:
                        self.log(f"❌ New user should have 0 credits, got {user_data['credits']}")
                        return False
                    if user_data['credit_rate_multiplier'] != 1.0:
                        self.log(f"❌ New user should have 1.0 multiplier, got {user_data['credit_rate_multiplier']}")
                        return False
                        
                else:
                    self.log(f"❌ Failed to create user {username}: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error creating user {username}: {str(e)}")
                return False
        
        # Test 2: Try to create duplicate username
        try:
            response = requests.post(
                f"{self.base_url}/users",
                json={"username": test_usernames[0]},
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
        
        # Test 3: Get all users
        try:
            response = requests.get(f"{self.base_url}/users", timeout=10)
            if response.status_code == 200:
                users = response.json()
                if len(users) >= len(test_usernames):
                    self.log(f"✅ Retrieved {len(users)} users successfully")
                else:
                    self.log(f"❌ Expected at least {len(test_usernames)} users, got {len(users)}")
                    return False
            else:
                self.log(f"❌ Failed to get users: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting users: {str(e)}")
            return False
        
        # Test 4: Get specific user
        if self.test_users:
            try:
                user_id = self.test_users[0]['id']
                response = requests.get(f"{self.base_url}/users/{user_id}", timeout=10)
                if response.status_code == 200:
                    user = response.json()
                    if user['id'] == user_id:
                        self.log("✅ Retrieved specific user successfully")
                    else:
                        self.log("❌ Retrieved user ID doesn't match requested ID")
                        return False
                else:
                    self.log(f"❌ Failed to get specific user: {response.status_code}")
                    return False
            except Exception as e:
                self.log(f"❌ Error getting specific user: {str(e)}")
                return False
        
        self.log("✅ User Management System tests passed")
        return True
    
    def test_focus_session_tracking(self):
        """Test Focus Session Tracking"""
        self.log("\n=== Testing Focus Session Tracking ===")
        
        if not self.test_users:
            self.log("❌ No test users available for focus session testing")
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
                self.test_sessions.append(session_data)
                self.log(f"✅ Started focus session for user {user['username']}")
                
                # Verify session structure
                required_fields = ['id', 'user_id', 'start_time', 'is_active']
                for field in required_fields:
                    if field not in session_data:
                        self.log(f"❌ Missing field '{field}' in session data")
                        return False
                
                if not session_data['is_active']:
                    self.log("❌ New session should be active")
                    return False
                    
            else:
                self.log(f"❌ Failed to start focus session: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error starting focus session: {str(e)}")
            return False
        
        # Test 2: Try to start another session (should fail)
        try:
            response = requests.post(
                f"{self.base_url}/focus/start",
                json={"user_id": user_id},
                timeout=10
            )
            if response.status_code == 400:
                self.log("✅ Prevented multiple active sessions correctly")
            else:
                self.log(f"❌ Should prevent multiple sessions, got {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing multiple sessions: {str(e)}")
            return False
        
        # Test 3: Get active users
        try:
            response = requests.get(f"{self.base_url}/focus/active", timeout=10)
            if response.status_code == 200:
                active_users = response.json()
                active_user_ids = [u['id'] for u in active_users]
                if user_id in active_user_ids:
                    self.log("✅ User appears in active users list")
                else:
                    self.log("❌ User should appear in active users list")
                    return False
            else:
                self.log(f"❌ Failed to get active users: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting active users: {str(e)}")
            return False
        
        # Test 4: Wait a bit and end session to test credit calculation
        self.log("Waiting 65 seconds to simulate focus time for proper credit calculation...")
        time.sleep(65)
        
        try:
            response = requests.post(
                f"{self.base_url}/focus/end",
                json={"user_id": user_id},
                timeout=10
            )
            
            if response.status_code == 200:
                end_data = response.json()
                self.log(f"✅ Ended focus session")
                
                # Verify credit calculation
                duration = end_data.get('duration_minutes', 0)
                credits_earned = end_data.get('credits_earned', 0)
                
                # Credits should be duration * multiplier (1.0 for new user)
                expected_credits = duration * 1.0
                if credits_earned == int(expected_credits):
                    self.log(f"✅ Credit calculation correct: {duration} min * 1.0 = {credits_earned} credits")
                else:
                    self.log(f"❌ Credit calculation wrong: expected {int(expected_credits)}, got {credits_earned}")
                    return False
                    
            else:
                self.log(f"❌ Failed to end focus session: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error ending focus session: {str(e)}")
            return False
        
        # Test 5: Verify user credits were updated
        try:
            response = requests.get(f"{self.base_url}/users/{user_id}", timeout=10)
            if response.status_code == 200:
                updated_user = response.json()
                if updated_user['credits'] > 0:
                    self.log(f"✅ User credits updated to {updated_user['credits']}")
                    # Update our test user data
                    for i, u in enumerate(self.test_users):
                        if u['id'] == user_id:
                            self.test_users[i] = updated_user
                            break
                else:
                    self.log("❌ User credits should be greater than 0 after focus session")
                    return False
            else:
                self.log(f"❌ Failed to get updated user: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting updated user: {str(e)}")
            return False
        
        self.log("✅ Focus Session Tracking tests passed")
        return True
    
    def test_shop_system(self):
        """Test Strategic Shop System"""
        self.log("\n=== Testing Strategic Shop System ===")
        
        # Test 1: Initialize shop items
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
        
        # Test 2: Get shop items
        try:
            response = requests.get(f"{self.base_url}/shop/items", timeout=10)
            if response.status_code == 200:
                self.shop_items = response.json()
                self.log(f"✅ Retrieved {len(self.shop_items)} shop items")
                
                # Verify item structure
                for item in self.shop_items:
                    required_fields = ['id', 'name', 'description', 'price', 'item_type', 'effect']
                    for field in required_fields:
                        if field not in item:
                            self.log(f"❌ Missing field '{field}' in shop item")
                            return False
                
                # Check for boost and sabotage items
                boost_items = [item for item in self.shop_items if item['item_type'] == 'boost']
                sabotage_items = [item for item in self.shop_items if item['item_type'] == 'sabotage']
                
                if not boost_items:
                    self.log("❌ No boost items found in shop")
                    return False
                if not sabotage_items:
                    self.log("❌ No sabotage items found in shop")
                    return False
                    
                self.log(f"✅ Found {len(boost_items)} boost items and {len(sabotage_items)} sabotage items")
                
            else:
                self.log(f"❌ Failed to get shop items: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting shop items: {str(e)}")
            return False
        
        if not self.test_users or len(self.test_users) < 2:
            self.log("❌ Need at least 2 users for shop testing")
            return False
        
        # Ensure users have enough credits for testing
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        
        # Give user1 more credits for testing purchases
        self.log("Setting up test credits for shop testing...")
        
        # Test 3: Purchase boost item
        boost_item = next((item for item in self.shop_items if item['item_type'] == 'boost'), None)
        if not boost_item:
            self.log("❌ No boost item available for testing")
            return False
        
        # First, let's give user1 enough credits by doing a focus session
        try:
            # Start session
            response = requests.post(
                f"{self.base_url}/focus/start",
                json={"user_id": user1['id']},
                timeout=10
            )
            if response.status_code == 200:
                time.sleep(2)  # Short focus session
                
                # End session
                response = requests.post(
                    f"{self.base_url}/focus/end",
                    json={"user_id": user1['id']},
                    timeout=10
                )
                
                # Get updated user
                response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
                if response.status_code == 200:
                    user1 = response.json()
                    self.test_users[0] = user1
                    self.log(f"User1 now has {user1['credits']} credits")
        except Exception as e:
            self.log(f"Warning: Could not set up credits: {str(e)}")
        
        # If still not enough credits, we'll test with insufficient credits scenario
        if user1['credits'] >= boost_item['price']:
            try:
                original_multiplier = user1['credit_rate_multiplier']
                
                response = requests.post(
                    f"{self.base_url}/shop/purchase",
                    json={
                        "user_id": user1['id'],
                        "item_id": boost_item['id']
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    purchase_data = response.json()
                    self.log(f"✅ Purchased boost item: {boost_item['name']}")
                    
                    # Verify user's multiplier increased
                    response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
                    if response.status_code == 200:
                        updated_user = response.json()
                        new_multiplier = updated_user['credit_rate_multiplier']
                        expected_multiplier = original_multiplier + boost_item['effect']['credit_rate_multiplier']
                        
                        if abs(new_multiplier - expected_multiplier) < 0.01:  # Float comparison
                            self.log(f"✅ Boost effect applied: multiplier {original_multiplier} → {new_multiplier}")
                            self.test_users[0] = updated_user
                        else:
                            self.log(f"❌ Boost effect not applied correctly: expected {expected_multiplier}, got {new_multiplier}")
                            return False
                    
                else:
                    self.log(f"❌ Failed to purchase boost item: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error purchasing boost item: {str(e)}")
                return False
        else:
            # Test insufficient credits scenario
            try:
                response = requests.post(
                    f"{self.base_url}/shop/purchase",
                    json={
                        "user_id": user1['id'],
                        "item_id": boost_item['id']
                    },
                    timeout=10
                )
                
                if response.status_code == 400:
                    self.log("✅ Insufficient credits handled correctly")
                else:
                    self.log(f"❌ Should return 400 for insufficient credits, got {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error testing insufficient credits: {str(e)}")
                return False
        
        # Test 4: Purchase sabotage item (if user has enough credits)
        sabotage_item = next((item for item in self.shop_items if item['item_type'] == 'sabotage'), None)
        if sabotage_item and user1['credits'] >= sabotage_item['price']:
            try:
                original_target_credits = user2['credits']
                original_target_multiplier = user2['credit_rate_multiplier']
                
                response = requests.post(
                    f"{self.base_url}/shop/purchase",
                    json={
                        "user_id": user1['id'],
                        "item_id": sabotage_item['id'],
                        "target_user_id": user2['id']
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Purchased sabotage item: {sabotage_item['name']}")
                    
                    # Verify sabotage effect on target user
                    response = requests.get(f"{self.base_url}/users/{user2['id']}", timeout=10)
                    if response.status_code == 200:
                        updated_target = response.json()
                        
                        effect = sabotage_item['effect']
                        if 'reset_credits' in effect and effect['reset_credits']:
                            if updated_target['credits'] == 0:
                                self.log("✅ Sabotage effect applied: credits reset to 0")
                            else:
                                self.log(f"❌ Credits should be reset to 0, got {updated_target['credits']}")
                                return False
                        
                        if 'reduce_multiplier' in effect:
                            expected_multiplier = max(0.1, original_target_multiplier - effect['reduce_multiplier'])
                            if abs(updated_target['credit_rate_multiplier'] - expected_multiplier) < 0.01:
                                self.log(f"✅ Sabotage effect applied: multiplier reduced to {updated_target['credit_rate_multiplier']}")
                            else:
                                self.log(f"❌ Multiplier reduction not applied correctly")
                                return False
                        
                        self.test_users[1] = updated_target
                    
                else:
                    self.log(f"❌ Failed to purchase sabotage item: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error purchasing sabotage item: {str(e)}")
                return False
        
        # Test 5: Get recent purchases
        try:
            response = requests.get(f"{self.base_url}/shop/purchases", timeout=10)
            if response.status_code == 200:
                purchases = response.json()
                self.log(f"✅ Retrieved {len(purchases)} recent purchases")
            else:
                self.log(f"❌ Failed to get purchases: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting purchases: {str(e)}")
            return False
        
        self.log("✅ Strategic Shop System tests passed")
        return True
    
    def test_leaderboard_system(self):
        """Test Leaderboard System"""
        self.log("\n=== Testing Leaderboard System ===")
        
        try:
            response = requests.get(f"{self.base_url}/leaderboard", timeout=10)
            if response.status_code == 200:
                leaderboard = response.json()
                self.log(f"✅ Retrieved leaderboard with {len(leaderboard)} users")
                
                # Verify leaderboard is sorted by credits (descending)
                if len(leaderboard) > 1:
                    for i in range(len(leaderboard) - 1):
                        if leaderboard[i]['credits'] < leaderboard[i + 1]['credits']:
                            self.log("❌ Leaderboard not sorted by credits descending")
                            return False
                    
                    self.log("✅ Leaderboard correctly sorted by credits")
                
                # Verify our test users appear in leaderboard
                leaderboard_ids = [user['id'] for user in leaderboard]
                test_user_ids = [user['id'] for user in self.test_users]
                
                for test_id in test_user_ids:
                    if test_id in leaderboard_ids:
                        self.log(f"✅ Test user {test_id} found in leaderboard")
                    else:
                        self.log(f"❌ Test user {test_id} not found in leaderboard")
                        return False
                
            else:
                self.log(f"❌ Failed to get leaderboard: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting leaderboard: {str(e)}")
            return False
        
        self.log("✅ Leaderboard System tests passed")
        return True
    
    def run_all_tests(self):
        """Run all test suites"""
        self.log("🚀 Starting Focus Royale Backend API Tests")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {
            "API Health": self.test_api_health(),
            "User Management": False,
            "Focus Session Tracking": False,
            "Strategic Shop System": False,
            "Leaderboard System": False
        }
        
        if test_results["API Health"]:
            test_results["User Management"] = self.test_user_management()
            
            if test_results["User Management"]:
                test_results["Focus Session Tracking"] = self.test_focus_session_tracking()
                test_results["Strategic Shop System"] = self.test_shop_system()
                test_results["Leaderboard System"] = self.test_leaderboard_system()
        
        # Print summary
        self.log("\n" + "="*50)
        self.log("TEST SUMMARY")
        self.log("="*50)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        self.log("="*50)
        if all_passed:
            self.log("🎉 ALL TESTS PASSED!")
        else:
            self.log("💥 SOME TESTS FAILED!")
        
        return test_results

if __name__ == "__main__":
    tester = FocusRoyaleAPITester()
    results = tester.run_all_tests()