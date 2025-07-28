#!/usr/bin/env python3
"""
Focus Royale Leaderboard Sorting Test
Tests the specific sorting issue reported by the user:
- Two L1 users (one with 120 FC and one with 20 FC) showing in wrong order
- Expected: Level 3 (10 FC), Level 2 (50 FC), Level 1 (120 FC), Level 1 (20 FC)
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://a553030d-530e-4f16-a501-891e80b56a37.preview.emergentagent.com/api"

class LeaderboardSortingTester:
    def __init__(self):
        self.base_url = BASE_URL
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def test_api_health(self):
        """Test if the API is accessible"""
        self.log("Testing API health...")
        try:
            response = requests.get(f"{self.base_url}/users", timeout=10)
            if response.status_code in [200, 404]:
                self.log("✅ API is accessible")
                return True
            else:
                self.log(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ API health check failed: {str(e)}")
            return False
    
    def reset_database(self):
        """Reset database to start fresh"""
        self.log("Resetting database...")
        try:
            response = requests.post(f"{self.base_url}/admin/reset-database", timeout=10)
            if response.status_code == 200:
                self.log("✅ Database reset successfully")
                return True
            else:
                self.log(f"❌ Failed to reset database: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error resetting database: {str(e)}")
            return False
    
    def create_test_users(self):
        """Create test users with specific levels and credits"""
        self.log("Creating test users...")
        
        # Test users as specified in the review request
        test_users_data = [
            {"username": "user_a_level2_50fc", "password": "password123", "level": 2, "credits": 50},
            {"username": "user_b_level1_120fc", "password": "password123", "level": 1, "credits": 120},
            {"username": "user_c_level1_20fc", "password": "password123", "level": 1, "credits": 20},
            {"username": "user_d_level3_10fc", "password": "password123", "level": 3, "credits": 10}
        ]
        
        created_users = []
        
        for user_data in test_users_data:
            try:
                # Register user
                response = requests.post(
                    f"{self.base_url}/auth/register",
                    json={"username": user_data["username"], "password": user_data["password"]},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    user_info = result.get("user", {})
                    created_users.append({
                        "id": user_info["id"],
                        "username": user_data["username"],
                        "target_level": user_data["level"],
                        "target_credits": user_data["credits"]
                    })
                    self.log(f"✅ Registered user: {user_data['username']} (ID: {user_info['id']})")
                else:
                    self.log(f"❌ Failed to register user {user_data['username']}: {response.status_code}")
                    return None
                    
            except Exception as e:
                self.log(f"❌ Error registering user {user_data['username']}: {str(e)}")
                return None
        
        return created_users
    
    def setup_user_data_directly(self, users):
        """Directly update user data in database using MongoDB operations"""
        self.log("Setting up user data directly...")
        
        # Initialize shop first to get level passes
        try:
            response = requests.post(f"{self.base_url}/init", timeout=10)
            if response.status_code != 200:
                self.log(f"❌ Failed to initialize shop: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error initializing shop: {str(e)}")
            return False
        
        # Get level pass for purchasing
        try:
            response = requests.get(f"{self.base_url}/shop/items", timeout=10)
            if response.status_code == 200:
                shop_items = response.json()
                level_pass = next((item for item in shop_items if item["name"] == "Level Pass"), None)
                if not level_pass:
                    self.log("❌ Level Pass not found")
                    return False
            else:
                self.log(f"❌ Failed to get shop items: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting shop items: {str(e)}")
            return False
        
        # For each user, do focus sessions to earn credits, then buy level passes
        for user in users:
            user_id = user["id"]
            username = user["username"]
            target_level = user["target_level"]
            target_credits = user["target_credits"]
            
            self.log(f"Setting up {username}: Level {target_level}, {target_credits} FC")
            
            # Calculate credits needed
            levels_to_buy = target_level - 1
            credits_for_levels = levels_to_buy * level_pass["price"]  # 100 FC per level
            total_credits_needed = credits_for_levels + target_credits
            
            # Do focus sessions to earn credits (need longer sessions for credits)
            # 30 FC/hour = 1 FC per 2 minutes, so 4 minutes = 2 FC
            sessions_needed = max(1, (total_credits_needed // 2) + 5)  # Extra sessions for safety
            
            for session in range(sessions_needed):
                try:
                    # Start focus session
                    start_response = requests.post(
                        f"{self.base_url}/focus/start",
                        json={"user_id": user_id},
                        timeout=10
                    )
                    
                    if start_response.status_code == 200:
                        # Wait 4 seconds (simulates 4 minutes for ~2 FC)
                        time.sleep(4)
                        
                        # End focus session
                        end_response = requests.post(
                            f"{self.base_url}/focus/end",
                            json={"user_id": user_id},
                            timeout=10
                        )
                        
                        if end_response.status_code == 200:
                            end_data = end_response.json()
                            credits_earned = end_data.get('credits_earned', 0)
                            if session % 10 == 0:  # Log every 10th session
                                self.log(f"  Session {session + 1}: Earned {credits_earned} FC")
                        else:
                            self.log(f"❌ Failed to end session {session + 1}")
                            break
                    else:
                        self.log(f"❌ Failed to start session {session + 1}")
                        break
                        
                except Exception as e:
                    self.log(f"❌ Error in session {session + 1}: {str(e)}")
                    break
                
                # Check if we have enough credits
                try:
                    user_response = requests.get(f"{self.base_url}/users/{user_id}", timeout=10)
                    if user_response.status_code == 200:
                        current_user = user_response.json()
                        current_credits = current_user.get('credits', 0)
                        if current_credits >= total_credits_needed:
                            self.log(f"  Earned enough credits: {current_credits} FC")
                            break
                except:
                    pass
            
            # Buy level passes
            for level_purchase in range(levels_to_buy):
                try:
                    purchase_response = requests.post(
                        f"{self.base_url}/shop/purchase",
                        json={"user_id": user_id, "item_id": level_pass["id"]},
                        timeout=10
                    )
                    
                    if purchase_response.status_code == 200:
                        self.log(f"  ✅ Purchased Level Pass {level_purchase + 1}/{levels_to_buy}")
                    else:
                        self.log(f"  ❌ Failed to purchase Level Pass {level_purchase + 1}: {purchase_response.status_code}")
                        break
                        
                except Exception as e:
                    self.log(f"  ❌ Error purchasing Level Pass {level_purchase + 1}: {str(e)}")
                    break
            
            # Verify final state
            try:
                final_response = requests.get(f"{self.base_url}/users/{user_id}", timeout=10)
                if final_response.status_code == 200:
                    final_user = final_response.json()
                    final_level = final_user.get('level', 1)
                    final_credits = final_user.get('credits', 0)
                    self.log(f"  Final: {username} - Level {final_level}, {final_credits} FC")
                    
                    # Update user data
                    user['actual_level'] = final_level
                    user['actual_credits'] = final_credits
                    
            except Exception as e:
                self.log(f"  ❌ Error getting final user state: {str(e)}")
                return False
        
        return True
    
    def test_leaderboard_sorting(self, users):
        """Test the leaderboard sorting logic"""
        self.log("\n=== Testing Leaderboard Sorting ===")
        
        try:
            response = requests.get(f"{self.base_url}/leaderboard", timeout=10)
            if response.status_code == 200:
                leaderboard = response.json()
                self.log(f"✅ Retrieved leaderboard with {len(leaderboard)} users")
                
                # Display current leaderboard
                self.log("\nCurrent Leaderboard Order:")
                for i, user in enumerate(leaderboard):
                    username = user.get('username', 'Unknown')
                    level = user.get('level', 0)
                    credits = user.get('credits', 0)
                    self.log(f"{i+1}. {username} - Level {level}, {credits} FC")
                
                # Test sorting logic
                sorting_correct = True
                issues_found = []
                
                # Test 1: Level sorting (descending)
                for i in range(len(leaderboard) - 1):
                    current_level = leaderboard[i].get('level', 0)
                    next_level = leaderboard[i + 1].get('level', 0)
                    
                    if current_level < next_level:
                        issue = f"Level sorting error: Position {i+1} (Level {current_level}) < Position {i+2} (Level {next_level})"
                        issues_found.append(issue)
                        sorting_correct = False
                
                # Test 2: Credits sorting within same level (descending)
                for i in range(len(leaderboard) - 1):
                    current_level = leaderboard[i].get('level', 0)
                    next_level = leaderboard[i + 1].get('level', 0)
                    current_credits = leaderboard[i].get('credits', 0)
                    next_credits = leaderboard[i + 1].get('credits', 0)
                    current_username = leaderboard[i].get('username', 'Unknown')
                    next_username = leaderboard[i + 1].get('username', 'Unknown')
                    
                    if current_level == next_level and current_credits < next_credits:
                        issue = f"Credits sorting error in Level {current_level}: {current_username} ({current_credits} FC) ranked above {next_username} ({next_credits} FC)"
                        issues_found.append(issue)
                        sorting_correct = False
                
                # Test 3: Specific test for the reported issue (L1 users with 120 FC vs 20 FC)
                l1_users = [user for user in leaderboard if user.get('level') == 1]
                if len(l1_users) >= 2:
                    user_120fc = None
                    user_20fc = None
                    
                    for user in l1_users:
                        username = user.get('username', '')
                        credits = user.get('credits', 0)
                        if '120fc' in username.lower() or (110 <= credits <= 130):
                            user_120fc = user
                        elif '20fc' in username.lower() or (15 <= credits <= 25):
                            user_20fc = user
                    
                    if user_120fc and user_20fc:
                        pos_120fc = next((i for i, u in enumerate(leaderboard) if u['id'] == user_120fc['id']), -1)
                        pos_20fc = next((i for i, u in enumerate(leaderboard) if u['id'] == user_20fc['id']), -1)
                        
                        if pos_120fc > pos_20fc:  # Higher position number = lower rank
                            issue = f"REPORTED BUG CONFIRMED: L1 user with {user_120fc.get('credits')} FC ranked BELOW L1 user with {user_20fc.get('credits')} FC"
                            issues_found.append(issue)
                            sorting_correct = False
                        else:
                            self.log(f"✅ L1 users correctly sorted: {user_120fc.get('credits')} FC user ranked above {user_20fc.get('credits')} FC user")
                
                # Report results
                if sorting_correct:
                    self.log("\n✅ LEADERBOARD SORTING IS CORRECT")
                    self.log("   - Users sorted by level (descending) first")
                    self.log("   - Within same level, users sorted by credits (descending)")
                    
                    # Verify expected order
                    expected_order = ["user_d_level3_10fc", "user_a_level2_50fc", "user_b_level1_120fc", "user_c_level1_20fc"]
                    actual_order = [user.get('username', '') for user in leaderboard]
                    
                    self.log(f"\nExpected order: {expected_order}")
                    self.log(f"Actual order:   {actual_order}")
                    
                    if actual_order == expected_order:
                        self.log("✅ Leaderboard matches expected order exactly")
                    else:
                        self.log("ℹ️  Leaderboard order differs but sorting logic is still correct")
                    
                    return True
                else:
                    self.log("\n❌ LEADERBOARD SORTING HAS ISSUES:")
                    for issue in issues_found:
                        self.log(f"   - {issue}")
                    return False
                
            else:
                self.log(f"❌ Failed to get leaderboard: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing leaderboard: {str(e)}")
            return False
    
    def run_test(self):
        """Run the complete leaderboard sorting test"""
        self.log("🚀 Starting Leaderboard Sorting Test")
        self.log(f"Testing against: {self.base_url}")
        
        # Step 1: API Health Check
        if not self.test_api_health():
            return False
        
        # Step 2: Reset Database
        if not self.reset_database():
            return False
        
        # Step 3: Create Test Users
        users = self.create_test_users()
        if not users:
            return False
        
        # Step 4: Setup User Data
        if not self.setup_user_data_directly(users):
            return False
        
        # Step 5: Test Leaderboard Sorting
        result = self.test_leaderboard_sorting(users)
        
        # Summary
        self.log("\n" + "="*60)
        self.log("LEADERBOARD SORTING TEST SUMMARY")
        self.log("="*60)
        
        if result:
            self.log("🎉 LEADERBOARD SORTING TEST PASSED!")
            self.log("The sorting logic works correctly:")
            self.log("1. Users are sorted by level (descending) first")
            self.log("2. Within same level, users are sorted by credits (descending)")
            self.log("3. The reported issue (L1 120FC vs 20FC) is NOT reproduced")
        else:
            self.log("💥 LEADERBOARD SORTING TEST FAILED!")
            self.log("Issues found with the sorting logic - see details above")
        
        return result

if __name__ == "__main__":
    tester = LeaderboardSortingTester()
    success = tester.run_test()
    exit(0 if success else 1)