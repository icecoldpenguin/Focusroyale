#!/usr/bin/env python3
"""
Focus Royale Backend API Test Suite - USER UPDATE ENDPOINT FOCUS
Tests the newly implemented user update endpoint and core app functionality:
- NEW USER UPDATE ENDPOINT (Critical Priority):
  * Username updates with uniqueness validation
  * Bio updates  
  * Profile picture updates (base64 format)
  * Password changes with current password verification
  * Error handling (user not found, username conflicts, incorrect passwords)
- Basic App Health Check
- Core Features Verification (authentication, focus sessions, social credit rate, shop/tasks)
"""

import requests
import json
import time
import uuid
import base64
from datetime import datetime, timedelta

# Backend URL from frontend/.env
BASE_URL = "https://449d00ec-bd67-4d50-be7e-3d093d40f27f.preview.emergentagent.com/api"

class FocusRoyaleUserUpdateAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_users = []
        self.test_passwords = []  # Store original passwords for testing
        
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
        """Test Authentication System with register/login"""
        self.log("\n=== Testing Authentication System ===")
        
        # Test 1: Register new users with passwords
        timestamp = int(time.time())
        test_users_data = [
            {"username": f"emma_focus_{timestamp}", "password": "secure_password_123"},
            {"username": f"david_productivity_{timestamp}", "password": "another_secure_pass"},
            {"username": f"sarah_zen_{timestamp}", "password": "zen_master_2024"}
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
                    self.test_passwords.append(user_data["password"])
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
                        
                else:
                    self.log(f"❌ Failed to register user {user_data['username']}: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error registering user {user_data['username']}: {str(e)}")
                return False
        
        self.log("✅ Authentication System tests passed")
        return True
    
    def test_user_update_endpoint(self):
        """Test NEW USER UPDATE ENDPOINT - CRITICAL PRIORITY"""
        self.log("\n=== 🔥 TESTING USER UPDATE ENDPOINT (CRITICAL) ===")
        
        if len(self.test_users) < 2:
            self.log("❌ Need at least 2 users for user update testing")
            return False
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        user1_password = self.test_passwords[0]
        
        # Test 1: Username Update with Uniqueness Validation
        self.log("\n--- Test 1: Username Update ---")
        
        # Test 1a: Valid username update
        new_username = f"updated_emma_{int(time.time())}"
        try:
            response = requests.put(
                f"{self.base_url}/users/update",
                json={
                    "user_id": user1["id"],
                    "username": new_username
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                updated_user = result.get("user", {})
                if updated_user.get("username") == new_username:
                    self.log(f"✅ Username updated successfully: {user1['username']} → {new_username}")
                    user1["username"] = new_username  # Update our local copy
                else:
                    self.log(f"❌ Username not updated in response: expected {new_username}, got {updated_user.get('username')}")
                    return False
            else:
                self.log(f"❌ Failed to update username: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error updating username: {str(e)}")
            return False
        
        # Test 1b: Try to update to existing username (should fail)
        try:
            response = requests.put(
                f"{self.base_url}/users/update",
                json={
                    "user_id": user1["id"],
                    "username": user2["username"]  # Try to use user2's username
                },
                timeout=10
            )
            
            if response.status_code == 400:
                self.log("✅ Username uniqueness validation working - duplicate username rejected")
            else:
                self.log(f"❌ Duplicate username should return 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing duplicate username: {str(e)}")
            return False
        
        # Test 2: Bio Update
        self.log("\n--- Test 2: Bio Update ---")
        
        new_bio = "I'm a productivity enthusiast who loves focus sessions! 🚀"
        try:
            response = requests.put(
                f"{self.base_url}/users/update",
                json={
                    "user_id": user1["id"],
                    "bio": new_bio
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                updated_user = result.get("user", {})
                if updated_user.get("bio") == new_bio:
                    self.log(f"✅ Bio updated successfully: '{new_bio}'")
                else:
                    self.log(f"❌ Bio not updated correctly: expected '{new_bio}', got '{updated_user.get('bio')}'")
                    return False
            else:
                self.log(f"❌ Failed to update bio: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error updating bio: {str(e)}")
            return False
        
        # Test 3: Profile Picture Update (Base64 format)
        self.log("\n--- Test 3: Profile Picture Update ---")
        
        # Create a simple base64 encoded image (1x1 pixel PNG)
        sample_base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
        
        try:
            response = requests.put(
                f"{self.base_url}/users/update",
                json={
                    "user_id": user1["id"],
                    "profile_picture": sample_base64_image
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                updated_user = result.get("user", {})
                if updated_user.get("profile_picture") == sample_base64_image:
                    self.log("✅ Profile picture updated successfully (base64 format)")
                else:
                    self.log("❌ Profile picture not updated correctly")
                    return False
            else:
                self.log(f"❌ Failed to update profile picture: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error updating profile picture: {str(e)}")
            return False
        
        # Test 4: Password Change with Current Password Verification
        self.log("\n--- Test 4: Password Change ---")
        
        # Test 4a: Valid password change
        new_password = "new_secure_password_456"
        try:
            response = requests.put(
                f"{self.base_url}/users/update",
                json={
                    "user_id": user1["id"],
                    "current_password": user1_password,
                    "new_password": new_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✅ Password updated successfully")
                user1_password = new_password  # Update our local copy
            else:
                self.log(f"❌ Failed to update password: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error updating password: {str(e)}")
            return False
        
        # Test 4b: Try password change with incorrect current password
        try:
            response = requests.put(
                f"{self.base_url}/users/update",
                json={
                    "user_id": user1["id"],
                    "current_password": "wrong_password",
                    "new_password": "another_new_password"
                },
                timeout=10
            )
            
            if response.status_code == 400:
                self.log("✅ Current password verification working - incorrect password rejected")
            else:
                self.log(f"❌ Incorrect current password should return 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing incorrect current password: {str(e)}")
            return False
        
        # Test 5: Error Handling - User Not Found
        self.log("\n--- Test 5: Error Handling ---")
        
        fake_user_id = str(uuid.uuid4())
        try:
            response = requests.put(
                f"{self.base_url}/users/update",
                json={
                    "user_id": fake_user_id,
                    "username": "test_username"
                },
                timeout=10
            )
            
            if response.status_code == 404:
                self.log("✅ User not found error handling working correctly")
            else:
                self.log(f"❌ Non-existent user should return 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing user not found: {str(e)}")
            return False
        
        # Test 6: Verify login with new password
        self.log("\n--- Test 6: Verify New Password Works ---")
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": user1["username"], "password": user1_password},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✅ Login successful with new password")
            else:
                self.log(f"❌ Failed to login with new password: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing login with new password: {str(e)}")
            return False
        
        # Test 7: Multiple field update in single request
        self.log("\n--- Test 7: Multiple Field Update ---")
        
        multi_update_bio = "Updated bio and username together! 🎯"
        multi_update_username = f"multi_update_{int(time.time())}"
        
        try:
            response = requests.put(
                f"{self.base_url}/users/update",
                json={
                    "user_id": user1["id"],
                    "username": multi_update_username,
                    "bio": multi_update_bio
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                updated_user = result.get("user", {})
                if (updated_user.get("username") == multi_update_username and 
                    updated_user.get("bio") == multi_update_bio):
                    self.log("✅ Multiple field update successful")
                else:
                    self.log("❌ Multiple field update failed")
                    return False
            else:
                self.log(f"❌ Failed multiple field update: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing multiple field update: {str(e)}")
            return False
        
        self.log("🎉 USER UPDATE ENDPOINT TESTS PASSED!")
        return True
    
    def test_social_credit_rate_system(self):
        """Test Social Credit Rate System (brief verification)"""
        self.log("\n=== Testing Social Credit Rate System ===")
        
        try:
            response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
            if response.status_code == 200:
                social_rate = response.json()
                self.log(f"✅ Social rate endpoint accessible: {social_rate.get('social_multiplier', 'N/A')}x multiplier")
                return True
            else:
                self.log(f"❌ Failed to get social rate: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing social rate: {str(e)}")
            return False
    
    def test_focus_session_tracking(self):
        """Test Focus Session Tracking (brief verification)"""
        self.log("\n=== Testing Focus Session Tracking ===")
        
        if not self.test_users:
            self.log("❌ No test users available for focus session testing")
            return False
        
        user = self.test_users[0]
        
        # Start focus session
        try:
            response = requests.post(
                f"{self.base_url}/focus/start",
                json={"user_id": user["id"]},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✅ Focus session started successfully")
                
                # End focus session after brief wait
                time.sleep(2)
                response = requests.post(
                    f"{self.base_url}/focus/end",
                    json={"user_id": user["id"]},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log("✅ Focus session ended successfully")
                    return True
                else:
                    self.log(f"❌ Failed to end focus session: {response.status_code}")
                    return False
            else:
                self.log(f"❌ Failed to start focus session: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing focus sessions: {str(e)}")
            return False
    
    def test_shop_system(self):
        """Test Shop System (brief verification)"""
        self.log("\n=== Testing Shop System ===")
        
        try:
            # Initialize shop
            response = requests.post(f"{self.base_url}/init", timeout=10)
            if response.status_code == 200:
                self.log("✅ Shop initialized successfully")
            
            # Get shop items
            response = requests.get(f"{self.base_url}/shop/items", timeout=10)
            if response.status_code == 200:
                items = response.json()
                self.log(f"✅ Retrieved {len(items)} shop items")
                return True
            else:
                self.log(f"❌ Failed to get shop items: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing shop system: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all test suites with focus on USER UPDATE ENDPOINT"""
        self.log("🚀 Starting Focus Royale Backend API Tests - USER UPDATE ENDPOINT FOCUS")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {
            "API Health": self.test_api_health(),
            "Database Reset": False,
            "Authentication System": False,
            "🔥 USER UPDATE ENDPOINT": False,  # CRITICAL PRIORITY
            "Social Credit Rate": False,
            "Focus Session Tracking": False,
            "Shop System": False
        }
        
        if test_results["API Health"]:
            test_results["Database Reset"] = self.test_database_reset()
            
            if test_results["Database Reset"]:
                test_results["Authentication System"] = self.test_authentication_system()
                
                if test_results["Authentication System"]:
                    # CRITICAL: Test the new user update endpoint
                    test_results["🔥 USER UPDATE ENDPOINT"] = self.test_user_update_endpoint()
                    
                    # Brief verification of existing features
                    test_results["Social Credit Rate"] = self.test_social_credit_rate_system()
                    test_results["Focus Session Tracking"] = self.test_focus_session_tracking()
                    test_results["Shop System"] = self.test_shop_system()
        
        # Print summary
        self.log("\n" + "="*70)
        self.log("USER UPDATE ENDPOINT FOCUS - TEST SUMMARY")
        self.log("="*70)
        
        all_passed = True
        critical_passed = True
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            priority = "🔥 CRITICAL" if "USER UPDATE" in test_name else ""
            self.log(f"{test_name}: {status} {priority}")
            
            if not result:
                all_passed = False
                if "USER UPDATE" in test_name:
                    critical_passed = False
        
        self.log("="*70)
        if critical_passed:
            self.log("🎉 CRITICAL USER UPDATE ENDPOINT TESTS PASSED!")
        else:
            self.log("💥 CRITICAL USER UPDATE ENDPOINT TESTS FAILED!")
            
        if all_passed:
            self.log("🎉 ALL TESTS PASSED!")
        else:
            self.log("💥 SOME TESTS FAILED!")
        
        return test_results

if __name__ == "__main__":
    tester = FocusRoyaleUserUpdateAPITester()
    results = tester.run_all_tests()