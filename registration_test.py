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
BASE_URL = "https://29ca1e8e-9c57-4a2c-9437-86ce9cfbfffc.preview.emergentagent.com/api"

class FocusRoyaleRegistrationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_users = []
        
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
    
    def test_user_registration_success(self):
        """Test successful user registration with unique usernames"""
        self.log("\n=== Testing User Registration Success ===")
        
        # Create realistic test users with unique usernames
        timestamp = int(time.time())
        test_users_data = [
            {"username": f"sarah_focus_{timestamp}", "password": "MySecurePass123!"},
            {"username": f"mike_productivity_{timestamp}", "password": "StudyHard2024@"},
            {"username": f"emma_zen_{timestamp}", "password": "FocusTime456#"}
        ]
        
        for user_data in test_users_data:
            try:
                self.log(f"Registering user: {user_data['username']}")
                response = requests.post(
                    f"{self.base_url}/auth/register",
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Verify response structure
                    if "user" not in result:
                        self.log("❌ Response missing 'user' field")
                        return False
                    
                    if "message" not in result:
                        self.log("❌ Response missing 'message' field")
                        return False
                    
                    user_info = result["user"]
                    message = result["message"]
                    
                    # Verify message
                    if message != "User registered successfully":
                        self.log(f"❌ Unexpected message: {message}")
                        return False
                    
                    self.test_users.append(user_info)
                    self.log(f"✅ Registered user: {user_data['username']} (ID: {user_info['id']})")
                    
                    # Verify user structure (password_hash should NOT be in response)
                    required_fields = ['id', 'username', 'credits', 'total_focus_time', 'level', 'credit_rate_multiplier', 'created_at']
                    for field in required_fields:
                        if field not in user_info:
                            self.log(f"❌ Missing required field '{field}' in user data")
                            return False
                    
                    # Verify password hash is NOT in response (security check)
                    if 'password_hash' in user_info:
                        self.log("❌ SECURITY ISSUE: Password hash should not be in response")
                        return False
                    
                    # Verify initial values are correct
                    if user_info['credits'] != 0:
                        self.log(f"❌ New user should have 0 credits, got {user_info['credits']}")
                        return False
                    
                    if user_info['credit_rate_multiplier'] != 1.0:
                        self.log(f"❌ New user should have 1.0 multiplier, got {user_info['credit_rate_multiplier']}")
                        return False
                    
                    if user_info['level'] != 1:
                        self.log(f"❌ New user should have level 1, got {user_info['level']}")
                        return False
                    
                    if user_info['total_focus_time'] != 0:
                        self.log(f"❌ New user should have 0 focus time, got {user_info['total_focus_time']}")
                        return False
                        
                else:
                    self.log(f"❌ Failed to register user {user_data['username']}: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error registering user {user_data['username']}: {str(e)}")
                return False
        
        self.log("✅ User registration success tests passed")
        return True
    
    def test_duplicate_username_prevention(self):
        """Test that duplicate username registration returns proper error"""
        self.log("\n=== Testing Duplicate Username Prevention ===")
        
        if not self.test_users:
            self.log("❌ No test users available for duplicate testing")
            return False
        
        # Try to register with the same username as the first test user
        duplicate_user_data = {
            "username": self.test_users[0]["username"],
            "password": "DifferentPassword123!"
        }
        
        try:
            self.log(f"Attempting to register duplicate username: {duplicate_user_data['username']}")
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=duplicate_user_data,
                timeout=10
            )
            
            if response.status_code == 400:
                result = response.json()
                if "detail" in result and "Username already exists" in result["detail"]:
                    self.log("✅ Duplicate username correctly rejected with proper error message")
                    return True
                else:
                    self.log(f"❌ Duplicate username rejected but wrong error message: {result}")
                    return False
            else:
                self.log(f"❌ Duplicate username should return 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing duplicate username: {str(e)}")
            return False
    
    def test_database_persistence(self):
        """Test that user data is properly saved to deployed MongoDB database"""
        self.log("\n=== Testing Database Persistence ===")
        
        if not self.test_users:
            self.log("❌ No test users available for persistence testing")
            return False
        
        # Test 1: Verify users appear in the users list
        try:
            response = requests.get(f"{self.base_url}/users", timeout=10)
            if response.status_code == 200:
                all_users = response.json()
                self.log(f"✅ Retrieved {len(all_users)} users from database")
                
                # Verify our test users are in the database
                test_user_ids = {user["id"] for user in self.test_users}
                db_user_ids = {user["id"] for user in all_users}
                
                if test_user_ids.issubset(db_user_ids):
                    self.log("✅ All test users found in database")
                else:
                    missing_users = test_user_ids - db_user_ids
                    self.log(f"❌ Missing users in database: {missing_users}")
                    return False
                    
            else:
                self.log(f"❌ Failed to retrieve users from database: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking database persistence: {str(e)}")
            return False
        
        # Test 2: Verify individual user retrieval
        for test_user in self.test_users:
            try:
                response = requests.get(f"{self.base_url}/users/{test_user['id']}", timeout=10)
                if response.status_code == 200:
                    db_user = response.json()
                    
                    # Verify key fields match
                    if db_user["username"] != test_user["username"]:
                        self.log(f"❌ Username mismatch for user {test_user['id']}")
                        return False
                    
                    if db_user["id"] != test_user["id"]:
                        self.log(f"❌ ID mismatch for user {test_user['id']}")
                        return False
                    
                    # Verify password hash is still not exposed
                    if 'password_hash' in db_user:
                        self.log("❌ SECURITY ISSUE: Password hash exposed in individual user retrieval")
                        return False
                    
                    self.log(f"✅ User {test_user['username']} correctly persisted in database")
                    
                else:
                    self.log(f"❌ Failed to retrieve user {test_user['id']}: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error retrieving user {test_user['id']}: {str(e)}")
                return False
        
        self.log("✅ Database persistence tests passed")
        return True
    
    def test_login_functionality(self):
        """Test that registered users can successfully log in"""
        self.log("\n=== Testing Login Functionality ===")
        
        if not self.test_users:
            self.log("❌ No test users available for login testing")
            return False
        
        # Test login for each registered user
        test_passwords = ["MySecurePass123!", "StudyHard2024@", "FocusTime456#"]
        
        for i, test_user in enumerate(self.test_users):
            try:
                login_data = {
                    "username": test_user["username"],
                    "password": test_passwords[i]
                }
                
                self.log(f"Testing login for user: {test_user['username']}")
                response = requests.post(
                    f"{self.base_url}/auth/login",
                    json=login_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Verify response structure
                    if "user" not in result or "message" not in result:
                        self.log("❌ Login response missing required fields")
                        return False
                    
                    if result["message"] != "Login successful":
                        self.log(f"❌ Unexpected login message: {result['message']}")
                        return False
                    
                    logged_in_user = result["user"]
                    
                    # Verify user data matches registration
                    if logged_in_user["id"] != test_user["id"]:
                        self.log(f"❌ Login returned wrong user ID")
                        return False
                    
                    if logged_in_user["username"] != test_user["username"]:
                        self.log(f"❌ Login returned wrong username")
                        return False
                    
                    # Verify password hash is still not exposed
                    if 'password_hash' in logged_in_user:
                        self.log("❌ SECURITY ISSUE: Password hash exposed in login response")
                        return False
                    
                    self.log(f"✅ Login successful for user: {test_user['username']}")
                    
                else:
                    self.log(f"❌ Login failed for user {test_user['username']}: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error testing login for user {test_user['username']}: {str(e)}")
                return False
        
        # Test invalid login credentials
        try:
            invalid_login = {
                "username": self.test_users[0]["username"],
                "password": "WrongPassword123!"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=invalid_login,
                timeout=10
            )
            
            if response.status_code == 401:
                result = response.json()
                if "detail" in result and "Invalid username or password" in result["detail"]:
                    self.log("✅ Invalid credentials correctly rejected")
                else:
                    self.log(f"❌ Invalid credentials rejected but wrong error message: {result}")
                    return False
            else:
                self.log(f"❌ Invalid credentials should return 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing invalid login: {str(e)}")
            return False
        
        self.log("✅ Login functionality tests passed")
        return True
    
    def run_registration_tests(self):
        """Run all registration-focused test suites"""
        self.log("🚀 Starting Focus Royale USER REGISTRATION Backend API Tests")
        self.log(f"Testing against: {self.base_url}")
        self.log("Focus: User registration functionality after MongoDB connection update")
        
        test_results = {
            "API Health": self.test_api_health(),
            "User Registration Success": False,
            "Duplicate Username Prevention": False,
            "Database Persistence": False,
            "Login Functionality": False
        }
        
        if test_results["API Health"]:
            test_results["User Registration Success"] = self.test_user_registration_success()
            
            if test_results["User Registration Success"]:
                test_results["Duplicate Username Prevention"] = self.test_duplicate_username_prevention()
                test_results["Database Persistence"] = self.test_database_persistence()
                test_results["Login Functionality"] = self.test_login_functionality()
        
        # Print summary
        self.log("\n" + "="*60)
        self.log("USER REGISTRATION TEST SUMMARY")
        self.log("="*60)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        self.log("="*60)
        if all_passed:
            self.log("🎉 ALL USER REGISTRATION TESTS PASSED!")
            self.log("✅ MongoDB connection is working correctly")
            self.log("✅ User registration endpoint is fully functional")
            self.log("✅ Database persistence is working as expected")
        else:
            self.log("💥 SOME USER REGISTRATION TESTS FAILED!")
            self.log("❌ There may be issues with MongoDB connection or registration logic")
        
        return test_results

if __name__ == "__main__":
    tester = FocusRoyaleRegistrationTester()
    results = tester.run_registration_tests()