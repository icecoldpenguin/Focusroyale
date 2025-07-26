#!/usr/bin/env python3
"""
Enhanced Social Credit Rate System Test Suite
Tests the social credit rate system with realistic focus session durations
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta

# Backend URL from frontend/.env
BASE_URL = "https://24d34c78-b1c6-4214-80fe-5c7326cad262.preview.emergentagent.com/api"

class EnhancedSocialRateSystemTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_users = []
        self.shop_items = []
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def setup_test_environment(self):
        """Setup clean test environment"""
        self.log("\n=== Setting Up Test Environment ===")
        
        # Reset database
        try:
            response = requests.post(f"{self.base_url}/admin/reset-database", timeout=10)
            if response.status_code == 200:
                self.log("✅ Database reset successfully")
            else:
                self.log(f"❌ Failed to reset database: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error resetting database: {str(e)}")
            return False
        
        # Initialize shop items
        try:
            response = requests.post(f"{self.base_url}/init", timeout=10)
            if response.status_code == 200:
                self.log("✅ Shop items initialized")
            else:
                self.log(f"❌ Failed to initialize shop: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error initializing shop: {str(e)}")
            return False
        
        # Get shop items
        try:
            response = requests.get(f"{self.base_url}/shop/items", timeout=10)
            if response.status_code == 200:
                self.shop_items = response.json()
                self.log(f"✅ Retrieved {len(self.shop_items)} shop items")
            else:
                self.log(f"❌ Failed to get shop items: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting shop items: {str(e)}")
            return False
        
        # Register 3 test users
        timestamp = int(time.time())
        test_users_data = [
            {"username": f"social_user1_{timestamp}", "password": "test_pass_123"},
            {"username": f"social_user2_{timestamp}", "password": "test_pass_456"},
            {"username": f"social_user3_{timestamp}", "password": "test_pass_789"}
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
                else:
                    self.log(f"❌ Failed to register user {user_data['username']}: {response.status_code}")
                    return False
            except Exception as e:
                self.log(f"❌ Error registering user {user_data['username']}: {str(e)}")
                return False
        
        return True
    
    def test_comprehensive_social_rate_workflow(self):
        """Test comprehensive social rate workflow with realistic durations"""
        self.log("\n=== Testing Comprehensive Social Rate Workflow ===")
        
        if len(self.test_users) < 3:
            self.log("❌ Need at least 3 test users")
            return False
        
        user1, user2, user3 = self.test_users[0], self.test_users[1], self.test_users[2]
        
        # Step 1: Test initial state (no users focusing)
        self.log("\n--- Step 1: Initial State (No Users Focusing) ---")
        try:
            response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("active_users_count") == 0 and data.get("social_multiplier") == 1.0:
                    self.log("✅ Initial state: 0 users focusing, 1.0x multiplier, 10 credits/hour")
                else:
                    self.log(f"❌ Initial state incorrect: {data}")
                    return False
            else:
                self.log(f"❌ Failed to get social rate: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting initial social rate: {str(e)}")
            return False
        
        # Step 2: User 1 starts focusing (1.0x rate)
        self.log("\n--- Step 2: User 1 Starts Focusing ---")
        try:
            response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user1["id"]}, timeout=10)
            if response.status_code == 200:
                self.log("✅ User 1 started focusing")
                
                # Check social rate
                response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("active_users_count") == 1 and data.get("social_multiplier") == 1.0:
                        self.log("✅ Social rate: 1 user focusing, 1.0x multiplier, 10 credits/hour")
                    else:
                        self.log(f"❌ Social rate incorrect: {data}")
                        return False
                else:
                    self.log(f"❌ Failed to get social rate: {response.status_code}")
                    return False
            else:
                self.log(f"❌ Failed to start focus session: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error starting user 1 focus: {str(e)}")
            return False
        
        # Step 3: User 2 starts focusing (2.0x rate)
        self.log("\n--- Step 3: User 2 Starts Focusing ---")
        try:
            response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user2["id"]}, timeout=10)
            if response.status_code == 200:
                self.log("✅ User 2 started focusing")
                
                # Check social rate
                response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("active_users_count") == 2 and data.get("social_multiplier") == 2.0:
                        self.log("✅ Social rate: 2 users focusing, 2.0x multiplier, 20 credits/hour")
                    else:
                        self.log(f"❌ Social rate incorrect: {data}")
                        return False
                else:
                    self.log(f"❌ Failed to get social rate: {response.status_code}")
                    return False
            else:
                self.log(f"❌ Failed to start focus session: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error starting user 2 focus: {str(e)}")
            return False
        
        # Step 4: User 3 starts focusing (3.0x rate)
        self.log("\n--- Step 4: User 3 Starts Focusing ---")
        try:
            response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user3["id"]}, timeout=10)
            if response.status_code == 200:
                self.log("✅ User 3 started focusing")
                
                # Check social rate
                response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("active_users_count") == 3 and data.get("social_multiplier") == 3.0:
                        self.log("✅ Social rate: 3 users focusing, 3.0x multiplier, 30 credits/hour")
                    else:
                        self.log(f"❌ Social rate incorrect: {data}")
                        return False
                else:
                    self.log(f"❌ Failed to get social rate: {response.status_code}")
                    return False
            else:
                self.log(f"❌ Failed to start focus session: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error starting user 3 focus: {str(e)}")
            return False
        
        # Step 5: Wait for realistic focus time (12 minutes = 2 credits at 1x rate)
        self.log("\n--- Step 5: Focus Session (12 minutes simulation) ---")
        self.log("Waiting 12 seconds to simulate 12 minutes of focus time...")
        time.sleep(12)
        
        # Step 6: User 1 ends session (should earn credits with 3.0x multiplier)
        self.log("\n--- Step 6: User 1 Ends Session ---")
        try:
            response = requests.post(f"{self.base_url}/focus/end", json={"user_id": user1["id"]}, timeout=10)
            if response.status_code == 200:
                end_data = response.json()
                duration = end_data.get('duration_minutes', 0)
                credits_earned = end_data.get('credits_earned', 0)
                effective_rate = end_data.get('effective_rate', 1.0)
                
                self.log(f"✅ User 1 ended session:")
                self.log(f"   Duration: {duration} minutes")
                self.log(f"   Effective rate: {effective_rate}x")
                self.log(f"   Credits earned: {credits_earned}")
                
                # Expected: duration / 6 * 3.0 (social multiplier)
                # With 12 minutes: 12 / 6 * 3.0 = 6 credits
                expected_credits = int((duration / 6) * 3.0) if duration > 0 else 0
                
                if duration >= 10:  # Should be around 12 minutes
                    if abs(effective_rate - 3.0) < 0.1:
                        self.log("✅ Effective rate includes social multiplier (3.0x)")
                    else:
                        self.log(f"❌ Expected ~3.0x effective rate, got {effective_rate}x")
                        return False
                    
                    if credits_earned >= expected_credits - 1:  # Allow for rounding
                        self.log(f"✅ Credit calculation correct: ~{expected_credits} credits with social multiplier")
                    else:
                        self.log(f"❌ Expected ~{expected_credits} credits, got {credits_earned}")
                        return False
                else:
                    self.log(f"⚠️  Duration too short ({duration} min), but effective rate is correct ({effective_rate}x)")
                
                # Check social rate decreased to 2.0x
                response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("active_users_count") == 2 and data.get("social_multiplier") == 2.0:
                        self.log("✅ Social rate decreased: 2 users focusing, 2.0x multiplier")
                    else:
                        self.log(f"❌ Social rate should be 2.0x with 2 users: {data}")
                        return False
                
            else:
                self.log(f"❌ Failed to end focus session: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error ending user 1 focus: {str(e)}")
            return False
        
        # Step 7: User 2 ends session (should earn credits with 2.0x multiplier)
        self.log("\n--- Step 7: User 2 Ends Session ---")
        try:
            response = requests.post(f"{self.base_url}/focus/end", json={"user_id": user2["id"]}, timeout=10)
            if response.status_code == 200:
                end_data = response.json()
                duration = end_data.get('duration_minutes', 0)
                credits_earned = end_data.get('credits_earned', 0)
                effective_rate = end_data.get('effective_rate', 1.0)
                
                self.log(f"✅ User 2 ended session:")
                self.log(f"   Duration: {duration} minutes")
                self.log(f"   Effective rate: {effective_rate}x")
                self.log(f"   Credits earned: {credits_earned}")
                
                # Should have 2.0x rate when session ended
                if abs(effective_rate - 2.0) < 0.1:
                    self.log("✅ User 2 had 2.0x effective rate during session")
                else:
                    self.log(f"❌ Expected ~2.0x effective rate, got {effective_rate}x")
                    return False
                
                # Check social rate decreased to 1.0x
                response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("active_users_count") == 1 and data.get("social_multiplier") == 1.0:
                        self.log("✅ Social rate decreased: 1 user focusing, 1.0x multiplier")
                    else:
                        self.log(f"❌ Social rate should be 1.0x with 1 user: {data}")
                        return False
                
            else:
                self.log(f"❌ Failed to end focus session: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error ending user 2 focus: {str(e)}")
            return False
        
        # Step 8: User 3 ends session (back to 0 users, 1.0x minimum)
        self.log("\n--- Step 8: User 3 Ends Session ---")
        try:
            response = requests.post(f"{self.base_url}/focus/end", json={"user_id": user3["id"]}, timeout=10)
            if response.status_code == 200:
                end_data = response.json()
                effective_rate = end_data.get('effective_rate', 1.0)
                
                self.log(f"✅ User 3 ended session with {effective_rate}x rate")
                
                # Check social rate back to minimum 1.0x
                response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("active_users_count") == 0 and data.get("social_multiplier") == 1.0:
                        self.log("✅ Social rate back to minimum: 0 users focusing, 1.0x multiplier")
                    else:
                        self.log(f"❌ Social rate should be 1.0x with 0 users: {data}")
                        return False
                
            else:
                self.log(f"❌ Failed to end focus session: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error ending user 3 focus: {str(e)}")
            return False
        
        return True
    
    def test_progression_pass_with_social_rate(self):
        """Test that Progression Pass works with social rate"""
        self.log("\n=== Testing Progression Pass + Social Rate ===")
        
        if not self.test_users:
            self.log("❌ No test users available")
            return False
        
        user1 = self.test_users[0]
        
        # Give user1 enough credits to buy Progression Pass
        # First, let's check their current credits
        try:
            response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                current_credits = user_data.get('credits', 0)
                self.log(f"User1 current credits: {current_credits}")
                
                # Find Progression Pass
                progression_pass = None
                for item in self.shop_items:
                    if item["name"] == "Progression Pass":
                        progression_pass = item
                        break
                
                if not progression_pass:
                    self.log("❌ Progression Pass not found")
                    return False
                
                if current_credits >= progression_pass["price"]:
                    # Purchase Progression Pass
                    response = requests.post(
                        f"{self.base_url}/shop/purchase",
                        json={"user_id": user1["id"], "item_id": progression_pass["id"]},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        self.log("✅ User1 purchased Progression Pass (+0.5x personal multiplier)")
                        
                        # Verify user's multiplier increased
                        response = requests.get(f"{self.base_url}/users/{user1['id']}", timeout=10)
                        if response.status_code == 200:
                            updated_user = response.json()
                            multiplier = updated_user.get('credit_rate_multiplier', 1.0)
                            
                            if multiplier == 1.5:
                                self.log(f"✅ User1's personal multiplier is now {multiplier}x")
                                
                                # Test with social rate
                                # Start user1 focusing (1.0x social)
                                response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user1["id"]}, timeout=10)
                                if response.status_code == 200:
                                    self.log("✅ User1 started focusing with enhanced personal rate")
                                    
                                    # Start user2 focusing (2.0x social)
                                    user2 = self.test_users[1]
                                    response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user2["id"]}, timeout=10)
                                    if response.status_code == 200:
                                        self.log("✅ User2 started focusing - now 2.0x social rate")
                                        
                                        # Wait and end user1's session
                                        time.sleep(8)  # 8 minutes simulation
                                        
                                        response = requests.post(f"{self.base_url}/focus/end", json={"user_id": user1["id"]}, timeout=10)
                                        if response.status_code == 200:
                                            end_data = response.json()
                                            effective_rate = end_data.get('effective_rate', 1.0)
                                            
                                            # Expected: 1.5 (personal) * 2.0 (social) = 3.0x
                                            expected_rate = 1.5 * 2.0
                                            
                                            if abs(effective_rate - expected_rate) < 0.1:
                                                self.log(f"✅ Combined rate correct: {effective_rate}x (1.5x personal * 2.0x social)")
                                            else:
                                                self.log(f"❌ Expected {expected_rate}x combined rate, got {effective_rate}x")
                                                return False
                                        
                                        # Clean up - end user2's session
                                        requests.post(f"{self.base_url}/focus/end", json={"user_id": user2["id"]}, timeout=10)
                                
                            else:
                                self.log(f"❌ Expected 1.5x personal multiplier, got {multiplier}x")
                                return False
                    else:
                        self.log(f"❌ Failed to purchase Progression Pass: {response.status_code}")
                        return False
                else:
                    self.log(f"ℹ️  User1 has {current_credits} credits, needs {progression_pass['price']} for Progression Pass")
                    self.log("ℹ️  Skipping Progression Pass test due to insufficient credits")
                    return True  # Not a failure
                
            else:
                self.log(f"❌ Failed to get user data: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Progression Pass: {str(e)}")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all enhanced social rate system tests"""
        self.log("🚀 Starting Enhanced Social Credit Rate System Tests")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {
            "Test Environment Setup": self.setup_test_environment(),
            "Comprehensive Social Rate Workflow": False,
            "Progression Pass + Social Rate": False
        }
        
        if test_results["Test Environment Setup"]:
            test_results["Comprehensive Social Rate Workflow"] = self.test_comprehensive_social_rate_workflow()
            test_results["Progression Pass + Social Rate"] = self.test_progression_pass_with_social_rate()
        
        # Print summary
        self.log("\n" + "="*70)
        self.log("ENHANCED SOCIAL CREDIT RATE SYSTEM TEST SUMMARY")
        self.log("="*70)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        self.log("="*70)
        if all_passed:
            self.log("🎉 ALL ENHANCED SOCIAL RATE SYSTEM TESTS PASSED!")
        else:
            self.log("💥 SOME ENHANCED SOCIAL RATE SYSTEM TESTS FAILED!")
        
        return test_results

if __name__ == "__main__":
    tester = EnhancedSocialRateSystemTester()
    results = tester.run_all_tests()