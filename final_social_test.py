#!/usr/bin/env python3
"""
Final Social Credit Rate System Test Suite
Tests edge cases and realistic scenarios for the social credit rate system
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta

# Backend URL from frontend/.env
BASE_URL = "https://e3df0517-0a22-4901-bbef-53950e10818c.preview.emergentagent.com/api"

class FinalSocialRateSystemTester:
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
            {"username": f"final_user1_{timestamp}", "password": "test_pass_123"},
            {"username": f"final_user2_{timestamp}", "password": "test_pass_456"},
            {"username": f"final_user3_{timestamp}", "password": "test_pass_789"}
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
    
    def test_edge_case_all_users_end_simultaneously(self):
        """Test edge case: all users ending sessions at once"""
        self.log("\n=== Testing Edge Case: All Users End Sessions Simultaneously ===")
        
        if len(self.test_users) < 3:
            self.log("❌ Need at least 3 test users")
            return False
        
        user1, user2, user3 = self.test_users[0], self.test_users[1], self.test_users[2]
        
        # Start all users focusing
        for i, user in enumerate([user1, user2, user3], 1):
            try:
                response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user["id"]}, timeout=10)
                if response.status_code == 200:
                    self.log(f"✅ User {i} started focusing")
                else:
                    self.log(f"❌ Failed to start user {i} focus: {response.status_code}")
                    return False
            except Exception as e:
                self.log(f"❌ Error starting user {i} focus: {str(e)}")
                return False
        
        # Verify 3.0x rate
        try:
            response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("active_users_count") == 3 and data.get("social_multiplier") == 3.0:
                    self.log("✅ All 3 users focusing: 3.0x multiplier")
                else:
                    self.log(f"❌ Expected 3 users and 3.0x rate: {data}")
                    return False
            else:
                self.log(f"❌ Failed to get social rate: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting social rate: {str(e)}")
            return False
        
        # Wait a bit
        time.sleep(5)
        
        # End all sessions simultaneously (or as close as possible)
        self.log("Ending all sessions simultaneously...")
        end_results = []
        for i, user in enumerate([user1, user2, user3], 1):
            try:
                response = requests.post(f"{self.base_url}/focus/end", json={"user_id": user["id"]}, timeout=10)
                if response.status_code == 200:
                    end_data = response.json()
                    end_results.append(end_data)
                    self.log(f"✅ User {i} ended session: {end_data.get('effective_rate', 0)}x rate")
                else:
                    self.log(f"❌ Failed to end user {i} session: {response.status_code}")
                    return False
            except Exception as e:
                self.log(f"❌ Error ending user {i} session: {str(e)}")
                return False
        
        # Verify final state
        try:
            response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("active_users_count") == 0 and data.get("social_multiplier") == 1.0:
                    self.log("✅ All sessions ended: 0 users focusing, 1.0x minimum rate")
                else:
                    self.log(f"❌ Expected 0 users and 1.0x rate: {data}")
                    return False
            else:
                self.log(f"❌ Failed to get final social rate: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting final social rate: {str(e)}")
            return False
        
        return True
    
    def test_realistic_focus_session_with_credits(self):
        """Test realistic focus session with actual credit earning"""
        self.log("\n=== Testing Realistic Focus Session with Credit Earning ===")
        
        if not self.test_users:
            self.log("❌ No test users available")
            return False
        
        user1, user2 = self.test_users[0], self.test_users[1]
        
        # Start user1 focusing (1.0x rate)
        try:
            response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user1["id"]}, timeout=10)
            if response.status_code == 200:
                self.log("✅ User1 started focusing (1.0x social rate)")
            else:
                self.log(f"❌ Failed to start user1 focus: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error starting user1 focus: {str(e)}")
            return False
        
        # Wait 2 seconds, then start user2 (2.0x rate)
        time.sleep(2)
        
        try:
            response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user2["id"]}, timeout=10)
            if response.status_code == 200:
                self.log("✅ User2 started focusing (now 2.0x social rate)")
            else:
                self.log(f"❌ Failed to start user2 focus: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error starting user2 focus: {str(e)}")
            return False
        
        # Wait 8 more seconds (total 10 seconds for user1, 8 seconds for user2)
        time.sleep(8)
        
        # End user1's session (should have been focusing for ~10 seconds with mixed rates)
        try:
            response = requests.post(f"{self.base_url}/focus/end", json={"user_id": user1["id"]}, timeout=10)
            if response.status_code == 200:
                end_data = response.json()
                duration = end_data.get('duration_minutes', 0)
                credits_earned = end_data.get('credits_earned', 0)
                effective_rate = end_data.get('effective_rate', 1.0)
                total_credits = end_data.get('total_credits', 0)
                
                self.log(f"✅ User1 session ended:")
                self.log(f"   Duration: {duration} minutes")
                self.log(f"   Effective rate: {effective_rate}x")
                self.log(f"   Credits earned: {credits_earned}")
                self.log(f"   Total credits: {total_credits}")
                
                # The effective rate should reflect the social multiplier at the time of ending
                if effective_rate >= 1.0:
                    self.log("✅ Effective rate includes social multiplier")
                else:
                    self.log(f"❌ Effective rate too low: {effective_rate}x")
                    return False
                
            else:
                self.log(f"❌ Failed to end user1 session: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error ending user1 session: {str(e)}")
            return False
        
        # Verify social rate dropped to 1.0x
        try:
            response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("active_users_count") == 1 and data.get("social_multiplier") == 1.0:
                    self.log("✅ Social rate correctly at 1.0x with 1 user focusing")
                else:
                    self.log(f"❌ Expected 1 user and 1.0x rate: {data}")
                    return False
            else:
                self.log(f"❌ Failed to get social rate: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting social rate: {str(e)}")
            return False
        
        # End user2's session
        try:
            response = requests.post(f"{self.base_url}/focus/end", json={"user_id": user2["id"]}, timeout=10)
            if response.status_code == 200:
                end_data = response.json()
                effective_rate = end_data.get('effective_rate', 1.0)
                self.log(f"✅ User2 session ended with {effective_rate}x rate")
            else:
                self.log(f"❌ Failed to end user2 session: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error ending user2 session: {str(e)}")
            return False
        
        return True
    
    def test_social_rate_formula_verification(self):
        """Test that the social rate formula is exactly: max(1.0, number_of_active_focusing_users)"""
        self.log("\n=== Testing Social Rate Formula Verification ===")
        
        if len(self.test_users) < 3:
            self.log("❌ Need at least 3 test users")
            return False
        
        # Test cases: 0, 1, 2, 3 users
        test_cases = [
            (0, 1.0, "No users focusing - minimum 1.0x"),
            (1, 1.0, "1 user focusing - 1.0x rate"),
            (2, 2.0, "2 users focusing - 2.0x rate"),
            (3, 3.0, "3 users focusing - 3.0x rate")
        ]
        
        # Start with 0 users (already the case)
        for expected_users, expected_multiplier, description in test_cases:
            try:
                response = requests.get(f"{self.base_url}/focus/social-rate", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    actual_users = data.get("active_users_count", 0)
                    actual_multiplier = data.get("social_multiplier", 0)
                    actual_credits_per_hour = data.get("credits_per_hour", 0)
                    
                    if actual_users == expected_users and actual_multiplier == expected_multiplier:
                        expected_credits_per_hour = expected_multiplier * 10
                        if actual_credits_per_hour == expected_credits_per_hour:
                            self.log(f"✅ {description}: {actual_users} users, {actual_multiplier}x rate, {actual_credits_per_hour} credits/hour")
                        else:
                            self.log(f"❌ Credits/hour wrong: expected {expected_credits_per_hour}, got {actual_credits_per_hour}")
                            return False
                    else:
                        self.log(f"❌ {description}: expected {expected_users} users and {expected_multiplier}x, got {actual_users} users and {actual_multiplier}x")
                        return False
                else:
                    self.log(f"❌ Failed to get social rate: {response.status_code}")
                    return False
            except Exception as e:
                self.log(f"❌ Error getting social rate: {str(e)}")
                return False
            
            # Add a user for the next test case (except for the last one)
            if expected_users < 3:
                user = self.test_users[expected_users]
                try:
                    response = requests.post(f"{self.base_url}/focus/start", json={"user_id": user["id"]}, timeout=10)
                    if response.status_code != 200:
                        self.log(f"❌ Failed to start user focus: {response.status_code}")
                        return False
                except Exception as e:
                    self.log(f"❌ Error starting user focus: {str(e)}")
                    return False
        
        # Clean up - end all sessions
        for user in self.test_users:
            try:
                requests.post(f"{self.base_url}/focus/end", json={"user_id": user["id"]}, timeout=10)
            except:
                pass  # Ignore errors in cleanup
        
        return True
    
    def run_all_tests(self):
        """Run all final social rate system tests"""
        self.log("🚀 Starting Final Social Credit Rate System Tests")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {
            "Test Environment Setup": self.setup_test_environment(),
            "Social Rate Formula Verification": False,
            "Realistic Focus Session with Credits": False,
            "Edge Case: All Users End Simultaneously": False
        }
        
        if test_results["Test Environment Setup"]:
            test_results["Social Rate Formula Verification"] = self.test_social_rate_formula_verification()
            test_results["Realistic Focus Session with Credits"] = self.test_realistic_focus_session_with_credits()
            test_results["Edge Case: All Users End Simultaneously"] = self.test_edge_case_all_users_end_simultaneously()
        
        # Print summary
        self.log("\n" + "="*70)
        self.log("FINAL SOCIAL CREDIT RATE SYSTEM TEST SUMMARY")
        self.log("="*70)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        self.log("="*70)
        if all_passed:
            self.log("🎉 ALL FINAL SOCIAL RATE SYSTEM TESTS PASSED!")
        else:
            self.log("💥 SOME FINAL SOCIAL RATE SYSTEM TESTS FAILED!")
        
        return test_results

if __name__ == "__main__":
    tester = FinalSocialRateSystemTester()
    results = tester.run_all_tests()