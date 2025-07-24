#!/usr/bin/env python3
"""
Focus Royale Backend API Test Suite - COMPREHENSIVE SHOP PASS TESTING
Tests all shop pass types with sufficient credits and comprehensive scenarios
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta

# Backend URL from frontend/.env
BASE_URL = "https://e3df0517-0a22-4901-bbef-53950e10818c.preview.emergentagent.com/api"

class ComprehensiveShopPassTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_users = []
        self.shop_items = []
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def setup_test_environment(self):
        """Setup test environment with users and credits"""
        self.log("🔧 Setting up test environment...")
        
        # Reset database
        try:
            response = requests.post(f"{self.base_url}/admin/reset-database", timeout=10)
            response = requests.post(f"{self.base_url}/init", timeout=10)
            self.log("✅ Database reset and shop initialized")
        except Exception as e:
            self.log(f"❌ Failed to setup environment: {str(e)}")
            return False
        
        # Create test users
        timestamp = int(time.time())
        test_users_data = [
            {"username": f"alice_tester_{timestamp}", "password": "test_pass_123"},
            {"username": f"bob_tester_{timestamp}", "password": "test_pass_456"}
        ]
        
        for user_data in test_users_data:
            try:
                response = requests.post(f"{self.base_url}/auth/register", json=user_data, timeout=10)
                if response.status_code == 200:
                    user_info = response.json()["user"]
                    self.test_users.append(user_info)
                    self.log(f"✅ Created user: {user_data['username']}")
                else:
                    self.log(f"❌ Failed to create user: {response.status_code}")
                    return False
            except Exception as e:
                self.log(f"❌ Error creating user: {str(e)}")
                return False
        
        # Give users credits by manually updating (simulating many completed tasks)
        for user in self.test_users:
            try:
                # Create and complete multiple tasks to give users enough credits
                for i in range(50):  # Create 50 tasks worth 150 credits each
                    task_data = {
                        "user_id": user["id"],
                        "title": f"Test task {i+1}",
                        "description": f"Test task {i+1} description"
                    }
                    
                    # Create task
                    response = requests.post(f"{self.base_url}/tasks", json=task_data, timeout=10)
                    if response.status_code == 200:
                        task = response.json()
                        
                        # Complete task
                        response = requests.post(
                            f"{self.base_url}/tasks/complete",
                            json={"user_id": user["id"], "task_id": task["id"]},
                            timeout=10
                        )
                        if response.status_code != 200:
                            break
                    else:
                        break
                
                # Get updated user data
                response = requests.get(f"{self.base_url}/users/{user['id']}", timeout=10)
                if response.status_code == 200:
                    updated_user = response.json()
                    self.test_users[self.test_users.index(user)] = updated_user
                    self.log(f"✅ User {user['username']} now has {updated_user['credits']} credits")
                
            except Exception as e:
                self.log(f"❌ Error giving credits to user: {str(e)}")
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
        
        return True
    
    def test_level_pass(self):
        """Test Level Pass: increases user level by 1"""
        self.log("\n=== Testing Level Pass ===")
        
        user = self.test_users[0]
        level_pass = next((item for item in self.shop_items if item["name"] == "Level Pass"), None)
        
        if not level_pass:
            self.log("❌ Level Pass not found")
            return False
        
        try:
            # Get current user state
            response = requests.get(f"{self.base_url}/users/{user['id']}", timeout=10)
            if response.status_code == 200:
                current_user = response.json()
                original_level = current_user['level']
                original_credits = current_user['credits']
            else:
                self.log(f"❌ Failed to get user state: {response.status_code}")
                return False
            
            # Purchase Level Pass
            response = requests.post(
                f"{self.base_url}/shop/purchase",
                json={"user_id": user["id"], "item_id": level_pass["id"]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Purchased Level Pass for {level_pass['price']} credits")
                
                # Verify level increased
                response = requests.get(f"{self.base_url}/users/{user['id']}", timeout=10)
                if response.status_code == 200:
                    updated_user = response.json()
                    
                    if updated_user['level'] == original_level + 1:
                        self.log(f"✅ Level increased from {original_level} to {updated_user['level']}")
                    else:
                        self.log(f"❌ Level not increased: expected {original_level + 1}, got {updated_user['level']}")
                        return False
                    
                    if updated_user['credits'] == original_credits - level_pass['price']:
                        self.log(f"✅ Credits correctly deducted: {original_credits} - {level_pass['price']} = {updated_user['credits']}")
                    else:
                        self.log(f"❌ Credits not deducted correctly")
                        return False
                    
                    # Update user data
                    self.test_users[0] = updated_user
                    
                else:
                    self.log(f"❌ Failed to get updated user: {response.status_code}")
                    return False
                
            else:
                self.log(f"❌ Failed to purchase Level Pass: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Level Pass: {str(e)}")
            return False
        
        self.log("✅ Level Pass test passed")
        return True
    
    def test_progression_pass(self):
        """Test Progression Pass: increases credit rate multiplier by +0.5x permanently"""
        self.log("\n=== Testing Progression Pass ===")
        
        user = self.test_users[0]
        progression_pass = next((item for item in self.shop_items if item["name"] == "Progression Pass"), None)
        
        if not progression_pass:
            self.log("❌ Progression Pass not found")
            return False
        
        try:
            # Get current user state
            response = requests.get(f"{self.base_url}/users/{user['id']}", timeout=10)
            if response.status_code == 200:
                current_user = response.json()
                original_multiplier = current_user['credit_rate_multiplier']
                original_credits = current_user['credits']
            else:
                self.log(f"❌ Failed to get user state: {response.status_code}")
                return False
            
            # Purchase Progression Pass
            response = requests.post(
                f"{self.base_url}/shop/purchase",
                json={"user_id": user["id"], "item_id": progression_pass["id"]},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log(f"✅ Purchased Progression Pass for {progression_pass['price']} credits")
                
                # Verify multiplier increased
                response = requests.get(f"{self.base_url}/users/{user['id']}", timeout=10)
                if response.status_code == 200:
                    updated_user = response.json()
                    expected_multiplier = original_multiplier + 0.5
                    
                    if abs(updated_user['credit_rate_multiplier'] - expected_multiplier) < 0.01:
                        self.log(f"✅ Multiplier increased from {original_multiplier} to {updated_user['credit_rate_multiplier']}")
                    else:
                        self.log(f"❌ Multiplier not increased correctly: expected {expected_multiplier}, got {updated_user['credit_rate_multiplier']}")
                        return False
                    
                    # Update user data
                    self.test_users[0] = updated_user
                    
                else:
                    self.log(f"❌ Failed to get updated user: {response.status_code}")
                    return False
                
            else:
                self.log(f"❌ Failed to purchase Progression Pass: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Progression Pass: {str(e)}")
            return False
        
        self.log("✅ Progression Pass test passed")
        return True
    
    def test_degression_pass(self):
        """Test Degression Pass: reduces target user's credit rate by -0.5x for 24 hours"""
        self.log("\n=== Testing Degression Pass ===")
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        degression_pass = next((item for item in self.shop_items if item["name"] == "Degression Pass"), None)
        
        if not degression_pass:
            self.log("❌ Degression Pass not found")
            return False
        
        try:
            # Get target user's current state
            response = requests.get(f"{self.base_url}/users/{user2['id']}", timeout=10)
            if response.status_code == 200:
                target_before = response.json()
                original_effects = target_before.get('active_effects', [])
            else:
                self.log(f"❌ Failed to get target user state: {response.status_code}")
                return False
            
            # Purchase Degression Pass targeting user2
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
                self.log(f"✅ Purchased Degression Pass targeting user2 for {degression_pass['price']} credits")
                
                # Verify target user has degression effect
                response = requests.get(f"{self.base_url}/users/{user2['id']}", timeout=10)
                if response.status_code == 200:
                    target_after = response.json()
                    active_effects = target_after.get('active_effects', [])
                    
                    # Look for degression effect
                    degression_effects = [e for e in active_effects if e.get('type') == 'degression']
                    if degression_effects:
                        effect = degression_effects[0]
                        self.log(f"✅ Degression effect applied to target user")
                        
                        # Verify effect details
                        if effect.get('rate_reduction') == 0.5:
                            self.log(f"✅ Correct rate reduction: {effect['rate_reduction']}")
                        else:
                            self.log(f"❌ Wrong rate reduction: expected 0.5, got {effect.get('rate_reduction')}")
                            return False
                        
                        if effect.get('applied_by') == user1['id']:
                            self.log(f"✅ Correct applier recorded")
                        else:
                            self.log(f"❌ Wrong applier: expected {user1['id']}, got {effect.get('applied_by')}")
                            return False
                        
                        # Verify expiration time (should be ~24 hours from now)
                        if 'expires_at' in effect:
                            self.log(f"✅ Expiration time set: {effect['expires_at']}")
                        else:
                            self.log(f"❌ No expiration time set")
                            return False
                        
                    else:
                        self.log(f"❌ No degression effect found on target user")
                        return False
                    
                else:
                    self.log(f"❌ Failed to get updated target user: {response.status_code}")
                    return False
                
                # Verify target user received notification
                response = requests.get(f"{self.base_url}/notifications/{user2['id']}", timeout=10)
                if response.status_code == 200:
                    notifications = response.json()
                    pass_notifications = [n for n in notifications if n.get("notification_type") == "pass_used"]
                    if pass_notifications:
                        self.log(f"✅ Target user received pass usage notification")
                    else:
                        self.log(f"❌ Target user did not receive notification")
                        return False
                
            else:
                self.log(f"❌ Failed to purchase Degression Pass: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Degression Pass: {str(e)}")
            return False
        
        self.log("✅ Degression Pass test passed")
        return True
    
    def test_reset_pass(self):
        """Test Reset Pass: resets target user's credits to 0"""
        self.log("\n=== Testing Reset Pass ===")
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        reset_pass = next((item for item in self.shop_items if item["name"] == "Reset Pass"), None)
        
        if not reset_pass:
            self.log("❌ Reset Pass not found")
            return False
        
        try:
            # Get target user's current credits
            response = requests.get(f"{self.base_url}/users/{user2['id']}", timeout=10)
            if response.status_code == 200:
                target_before = response.json()
                original_credits = target_before['credits']
                self.log(f"Target user has {original_credits} credits before reset")
            else:
                self.log(f"❌ Failed to get target user state: {response.status_code}")
                return False
            
            # Purchase Reset Pass targeting user2
            response = requests.post(
                f"{self.base_url}/shop/purchase",
                json={
                    "user_id": user1["id"],
                    "item_id": reset_pass["id"],
                    "target_user_id": user2["id"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.log(f"✅ Purchased Reset Pass targeting user2 for {reset_pass['price']} credits")
                
                # Verify target user's credits reset to 0
                response = requests.get(f"{self.base_url}/users/{user2['id']}", timeout=10)
                if response.status_code == 200:
                    target_after = response.json()
                    
                    if target_after['credits'] == 0:
                        self.log(f"✅ Target user's credits reset from {original_credits} to 0")
                    else:
                        self.log(f"❌ Target user's credits not reset: expected 0, got {target_after['credits']}")
                        return False
                    
                else:
                    self.log(f"❌ Failed to get updated target user: {response.status_code}")
                    return False
                
            else:
                self.log(f"❌ Failed to purchase Reset Pass: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Reset Pass: {str(e)}")
            return False
        
        self.log("✅ Reset Pass test passed")
        return True
    
    def test_ally_token(self):
        """Test Ally Token: gives both users +1x credit rate for 3 hours"""
        self.log("\n=== Testing Ally Token ===")
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        ally_token = next((item for item in self.shop_items if item["name"] == "Ally Token"), None)
        
        if not ally_token:
            self.log("❌ Ally Token not found")
            return False
        
        try:
            # Purchase Ally Token targeting user2
            response = requests.post(
                f"{self.base_url}/shop/purchase",
                json={
                    "user_id": user1["id"],
                    "item_id": ally_token["id"],
                    "target_user_id": user2["id"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.log(f"✅ Purchased Ally Token targeting user2 for {ally_token['price']} credits")
                
                # Verify both users have ally boost effect
                for i, user in enumerate([user1, user2]):
                    response = requests.get(f"{self.base_url}/users/{user['id']}", timeout=10)
                    if response.status_code == 200:
                        user_data = response.json()
                        active_effects = user_data.get('active_effects', [])
                        
                        # Look for ally boost effect
                        ally_effects = [e for e in active_effects if e.get('type') == 'ally_boost']
                        if ally_effects:
                            effect = ally_effects[0]
                            self.log(f"✅ User{i+1} has ally boost effect")
                            
                            # Verify effect details
                            if effect.get('rate_boost') == 1.0:
                                self.log(f"✅ Correct rate boost: {effect['rate_boost']}")
                            else:
                                self.log(f"❌ Wrong rate boost: expected 1.0, got {effect.get('rate_boost')}")
                                return False
                            
                            # Verify expiration time (should be ~3 hours from now)
                            if 'expires_at' in effect:
                                self.log(f"✅ Expiration time set: {effect['expires_at']}")
                            else:
                                self.log(f"❌ No expiration time set")
                                return False
                            
                        else:
                            self.log(f"❌ User{i+1} does not have ally boost effect")
                            return False
                    else:
                        self.log(f"❌ Failed to get user{i+1} data: {response.status_code}")
                        return False
                
                # Verify target user received notification
                response = requests.get(f"{self.base_url}/notifications/{user2['id']}", timeout=10)
                if response.status_code == 200:
                    notifications = response.json()
                    ally_notifications = [n for n in notifications if n.get("notification_type") == "ally_formed"]
                    if ally_notifications:
                        self.log(f"✅ Target user received ally formation notification")
                    else:
                        self.log(f"❌ Target user did not receive ally notification")
                        return False
                
            else:
                self.log(f"❌ Failed to purchase Ally Token: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Ally Token: {str(e)}")
            return False
        
        self.log("✅ Ally Token test passed")
        return True
    
    def test_trade_pass(self):
        """Test Trade Pass: creates trade request (requires mutual consent)"""
        self.log("\n=== Testing Trade Pass ===")
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        trade_pass = next((item for item in self.shop_items if item["name"] == "Trade Pass"), None)
        
        if not trade_pass:
            self.log("❌ Trade Pass not found")
            return False
        
        try:
            # Purchase Trade Pass targeting user2
            response = requests.post(
                f"{self.base_url}/shop/purchase",
                json={
                    "user_id": user1["id"],
                    "item_id": trade_pass["id"],
                    "target_user_id": user2["id"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Purchased Trade Pass targeting user2 for {trade_pass['price']} credits")
                
                # Verify trade requires consent
                if result.get('requires_consent'):
                    self.log(f"✅ Trade Pass correctly requires mutual consent")
                else:
                    self.log(f"❌ Trade Pass should require mutual consent")
                    return False
                
                # Verify purchase ID provided for consent tracking
                if result.get('purchase_id'):
                    self.log(f"✅ Purchase ID provided for consent tracking: {result['purchase_id']}")
                else:
                    self.log(f"❌ No purchase ID provided for consent tracking")
                    return False
                
            else:
                self.log(f"❌ Failed to purchase Trade Pass: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Trade Pass: {str(e)}")
            return False
        
        self.log("✅ Trade Pass test passed")
        return True
    
    def test_targeting_validation(self):
        """Test targeting system validation"""
        self.log("\n=== Testing Targeting System Validation ===")
        
        user1 = self.test_users[0]
        degression_pass = next((item for item in self.shop_items if item["name"] == "Degression Pass"), None)
        
        if not degression_pass:
            self.log("❌ Degression Pass not found for targeting test")
            return False
        
        try:
            # Test 1: Pass requiring target without target should fail
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
                self.log("✅ Pass requiring target correctly fails without target")
            else:
                self.log(f"❌ Expected 400 for missing target, got {response.status_code}")
                return False
            
            # Test 2: Pass with non-existent target should fail
            fake_user_id = str(uuid.uuid4())
            response = requests.post(
                f"{self.base_url}/shop/purchase",
                json={
                    "user_id": user1["id"],
                    "item_id": degression_pass["id"],
                    "target_user_id": fake_user_id
                },
                timeout=10
            )
            
            if response.status_code == 404:
                self.log("✅ Pass with non-existent target correctly fails")
            else:
                self.log(f"❌ Expected 404 for non-existent target, got {response.status_code}")
                return False
            
        except Exception as e:
            self.log(f"❌ Error testing targeting validation: {str(e)}")
            return False
        
        self.log("✅ Targeting validation tests passed")
        return True
    
    def test_insufficient_credits(self):
        """Test credit deduction and insufficient credits handling"""
        self.log("\n=== Testing Credit Deduction and Insufficient Credits ===")
        
        # Create a new user with minimal credits
        timestamp = int(time.time())
        poor_user_data = {"username": f"poor_user_{timestamp}", "password": "test_pass"}
        
        try:
            response = requests.post(f"{self.base_url}/auth/register", json=poor_user_data, timeout=10)
            if response.status_code == 200:
                poor_user = response.json()["user"]
                self.log(f"✅ Created poor user with {poor_user['credits']} credits")
            else:
                self.log(f"❌ Failed to create poor user: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error creating poor user: {str(e)}")
            return False
        
        # Try to purchase expensive item
        reset_pass = next((item for item in self.shop_items if item["name"] == "Reset Pass"), None)
        if not reset_pass:
            self.log("❌ Reset Pass not found for insufficient credits test")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/shop/purchase",
                json={
                    "user_id": poor_user["id"],
                    "item_id": reset_pass["id"],
                    "target_user_id": self.test_users[0]["id"]
                },
                timeout=10
            )
            
            if response.status_code == 400:
                self.log("✅ Insufficient credits correctly handled")
            else:
                self.log(f"❌ Expected 400 for insufficient credits, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing insufficient credits: {str(e)}")
            return False
        
        self.log("✅ Credit deduction tests passed")
        return True
    
    def run_comprehensive_shop_tests(self):
        """Run all comprehensive shop pass tests"""
        self.log("🚀 Starting Comprehensive Shop Pass Tests")
        self.log(f"Testing against: {self.base_url}")
        
        # Setup test environment
        if not self.setup_test_environment():
            self.log("❌ Failed to setup test environment")
            return False
        
        test_results = {
            "Level Pass": self.test_level_pass(),
            "Progression Pass": self.test_progression_pass(),
            "Degression Pass": self.test_degression_pass(),
            "Reset Pass": self.test_reset_pass(),
            "Ally Token": self.test_ally_token(),
            "Trade Pass": self.test_trade_pass(),
            "Targeting Validation": self.test_targeting_validation(),
            "Credit Deduction": self.test_insufficient_credits()
        }
        
        # Print summary
        self.log("\n" + "="*60)
        self.log("COMPREHENSIVE SHOP PASS TEST SUMMARY")
        self.log("="*60)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        self.log("="*60)
        if all_passed:
            self.log("🎉 ALL COMPREHENSIVE SHOP PASS TESTS PASSED!")
        else:
            self.log("💥 SOME TESTS FAILED!")
        
        return test_results

if __name__ == "__main__":
    tester = ComprehensiveShopPassTester()
    results = tester.run_comprehensive_shop_tests()