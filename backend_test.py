#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Binance Trading Bot
Tests all backend endpoints systematically
"""

import requests
import json
import time
import asyncio
import websockets
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://00b9d56b-566d-4744-8187-80617fe7456d.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class BinanceBotTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """Test basic health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_test("Health Check", True, "Backend is healthy")
                    return True
                else:
                    self.log_test("Health Check", False, "Invalid health response format", data)
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            # Use realistic test data
            test_user = {
                "name": "Alice Johnson",
                "email": "alice.johnson@example.com",
                "password": "SecurePass123!"
            }
            
            response = self.session.post(f"{API_BASE}/register", json=test_user, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["access_token", "token_type", "user"]
                
                if all(field in data for field in required_fields):
                    self.auth_token = data["access_token"]
                    self.user_data = data["user"]
                    self.log_test("User Registration", True, "User registered successfully")
                    return True
                else:
                    self.log_test("User Registration", False, "Missing required fields in response", data)
                    return False
            elif response.status_code == 400:
                # User might already exist, try login instead
                return self.test_user_login_existing()
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Request error: {str(e)}")
            return False
    
    def test_user_login_existing(self):
        """Test login with existing user"""
        try:
            login_data = {
                "email": "alice.johnson@example.com",
                "password": "SecurePass123!"
            }
            
            response = self.session.post(f"{API_BASE}/login", json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["access_token", "token_type", "user"]
                
                if all(field in data for field in required_fields):
                    self.auth_token = data["access_token"]
                    self.user_data = data["user"]
                    self.log_test("User Login", True, "User logged in successfully")
                    return True
                else:
                    self.log_test("User Login", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Request error: {str(e)}")
            return False
    
    def test_protected_route_auth(self):
        """Test JWT authentication on protected routes"""
        if not self.auth_token:
            self.log_test("Protected Route Auth", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{API_BASE}/user/profile", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "email", "name", "subscription"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Protected Route Auth", True, "JWT authentication working")
                    return True
                else:
                    self.log_test("Protected Route Auth", False, "Missing required fields", data)
                    return False
            else:
                self.log_test("Protected Route Auth", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Protected Route Auth", False, f"Request error: {str(e)}")
            return False
    
    def test_coin_data_api(self):
        """Test real-time coin data API with EMA calculations"""
        try:
            response = self.session.get(f"{API_BASE}/coins", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "coins" in data and "timestamp" in data:
                    coins = data["coins"]
                    if len(coins) > 0:
                        # Check first coin has required fields
                        coin = coins[0]
                        required_fields = ["symbol", "price", "change_24h", "volume_24h", "ema9", "ema21", "signal"]
                        
                        if all(field in coin for field in required_fields):
                            # Validate signal values
                            valid_signals = ["BUY", "SELL", "STRONG_BUY", "STRONG_SELL"]
                            if coin["signal"] in valid_signals:
                                self.log_test("Coin Data API", True, f"Retrieved {len(coins)} coins with EMA data")
                                return True
                            else:
                                self.log_test("Coin Data API", False, f"Invalid signal value: {coin['signal']}")
                                return False
                        else:
                            missing = [f for f in required_fields if f not in coin]
                            self.log_test("Coin Data API", False, f"Missing fields: {missing}", coin)
                            return False
                    else:
                        self.log_test("Coin Data API", False, "No coins returned")
                        return False
                else:
                    self.log_test("Coin Data API", False, "Missing coins or timestamp in response", data)
                    return False
            else:
                self.log_test("Coin Data API", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Coin Data API", False, f"Request error: {str(e)}")
            return False
    
    def test_bot_config_crud(self):
        """Test bot configuration CRUD operations"""
        if not self.auth_token:
            self.log_test("Bot Config CRUD", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Test GET (read) - should return default config
            response = self.session.get(f"{API_BASE}/bot/config", headers=headers, timeout=10)
            
            if response.status_code == 200:
                config = response.json()
                required_fields = ["symbol", "timeframe", "leverage", "take_profit", "stop_loss", "position_size"]
                
                if all(field in config for field in required_fields):
                    self.log_test("Bot Config GET", True, "Retrieved bot configuration")
                    
                    # Test PUT (update)
                    updated_config = {
                        "symbol": "ETHUSDT",
                        "timeframe": "5m",
                        "leverage": 2,
                        "take_profit": 3.0,
                        "stop_loss": 1.5,
                        "position_size": 20.0
                    }
                    
                    response = self.session.put(f"{API_BASE}/bot/config", json=updated_config, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # Verify update by reading again
                        response = self.session.get(f"{API_BASE}/bot/config", headers=headers, timeout=10)
                        if response.status_code == 200:
                            updated_data = response.json()
                            if updated_data["symbol"] == "ETHUSDT" and updated_data["leverage"] == 2:
                                self.log_test("Bot Config CRUD", True, "Bot configuration CRUD operations working")
                                return True
                            else:
                                self.log_test("Bot Config CRUD", False, "Configuration not updated properly", updated_data)
                                return False
                        else:
                            self.log_test("Bot Config CRUD", False, "Failed to verify update")
                            return False
                    else:
                        self.log_test("Bot Config CRUD", False, f"PUT failed: HTTP {response.status_code}", response.text)
                        return False
                else:
                    missing = [f for f in required_fields if f not in config]
                    self.log_test("Bot Config CRUD", False, f"Missing fields: {missing}", config)
                    return False
            else:
                self.log_test("Bot Config CRUD", False, f"GET failed: HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Bot Config CRUD", False, f"Request error: {str(e)}")
            return False
    
    def test_bot_control_endpoints(self):
        """Test bot start/stop endpoints with subscription validation"""
        if not self.auth_token:
            self.log_test("Bot Control", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Test start bot (should fail due to no active subscription)
            response = self.session.post(f"{API_BASE}/bot/start", headers=headers, timeout=10)
            
            if response.status_code == 403:
                # Expected - no active subscription
                self.log_test("Bot Start (No Subscription)", True, "Correctly blocked start without subscription")
                
                # Test stop bot (should work regardless of subscription)
                response = self.session.post(f"{API_BASE}/bot/stop", headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if "message" in data:
                        self.log_test("Bot Control Endpoints", True, "Bot control endpoints working with proper validation")
                        return True
                    else:
                        self.log_test("Bot Control Endpoints", False, "Stop response missing message", data)
                        return False
                else:
                    self.log_test("Bot Control Endpoints", False, f"Stop failed: HTTP {response.status_code}", response.text)
                    return False
            else:
                self.log_test("Bot Control Endpoints", False, f"Start should fail with 403, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Bot Control Endpoints", False, f"Request error: {str(e)}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket real-time data stream"""
        try:
            ws_url = f"{BACKEND_URL.replace('https://', 'wss://')}/api/ws"
            
            async with websockets.connect(ws_url, timeout=15) as websocket:
                # Wait for first message
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(message)
                
                if data.get("type") == "coins_update" and "data" in data:
                    coins = data["data"]
                    if len(coins) > 0:
                        coin = coins[0]
                        required_fields = ["symbol", "price", "ema9", "ema21", "signal"]
                        
                        if all(field in coin for field in required_fields):
                            self.log_test("WebSocket Connection", True, f"Received real-time data for {len(coins)} coins")
                            return True
                        else:
                            missing = [f for f in required_fields if f not in coin]
                            self.log_test("WebSocket Connection", False, f"Missing fields in WebSocket data: {missing}")
                            return False
                    else:
                        self.log_test("WebSocket Connection", False, "No coins in WebSocket data")
                        return False
                else:
                    self.log_test("WebSocket Connection", False, "Invalid WebSocket message format", data)
                    return False
                    
        except asyncio.TimeoutError:
            self.log_test("WebSocket Connection", False, "WebSocket connection timeout")
            return False
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"WebSocket error: {str(e)}")
            return False
    
    def run_websocket_test(self):
        """Run WebSocket test in event loop"""
        try:
            return asyncio.run(self.test_websocket_connection())
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Event loop error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Binance Trading Bot Backend API Tests")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration/Login", self.test_user_registration),
            ("JWT Authentication", self.test_protected_route_auth),
            ("Coin Data API", self.test_coin_data_api),
            ("Bot Configuration CRUD", self.test_bot_config_crud),
            ("Bot Control Endpoints", self.test_bot_control_endpoints),
            ("WebSocket Real-time Stream", self.run_websocket_test),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All backend tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} tests FAILED")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
            return False

def main():
    """Main test execution"""
    tester = BinanceBotTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())