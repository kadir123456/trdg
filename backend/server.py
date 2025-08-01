from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
import bcrypt
import jwt
from jose import JWTError
import json
import asyncio
import websockets
import requests
import pandas as pd
import numpy as np
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None
import uuid
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Binance Trading Bot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    raise ValueError("MONGO_URL environment variable is required")

client = MongoClient(MONGO_URL)
db_name = os.environ.get('DB_NAME', 'trading_bot_db')
db = client[db_name]

# Collections
users_collection = db.users
sessions_collection = db.sessions
bot_configs_collection = db.bot_configs
trades_collection = db.trades
subscriptions_collection = db.subscriptions

# JWT and security
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your_secret_key')
JWT_ALGORITHM = "HS256"

# Binance configuration (placeholder)
BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY', 'placeholder_key')
BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET', 'placeholder_secret')

# Initialize Binance client with testnet for development
if BINANCE_AVAILABLE and BINANCE_API_KEY != 'placeholder_key':
    try:
        binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)
    except Exception as e:
        logger.error(f"Binance client initialization failed: {e}")
        binance_client = None
else:
    binance_client = None
    logger.info("Using mock data - Binance API not configured")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class BotConfig(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "1m"
    leverage: int = 1
    take_profit: float = 2.0
    stop_loss: float = 1.0
    position_size: float = 10.0

class ApiKeyUpdate(BaseModel):
    api_key: str
    api_secret: str

class CoinData(BaseModel):
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    ema9: Optional[float] = None
    ema21: Optional[float] = None
    signal: Optional[str] = None

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = users_collection.find_one({"user_id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def calculate_ema(prices: List[float], period: int) -> List[float]:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return [0] * len(prices)
    
    prices_series = pd.Series(prices)
    ema = prices_series.ewm(span=period).mean()
    return ema.tolist()

def get_trading_signal(ema9: float, ema21: float, prev_ema9: float, prev_ema21: float) -> str:
    """Generate trading signal based on EMA crossover"""
    current_signal = "BUY" if ema9 > ema21 else "SELL"
    prev_signal = "BUY" if prev_ema9 > prev_ema21 else "SELL"
    
    if current_signal == "BUY" and prev_signal == "SELL":
        return "STRONG_BUY"
    elif current_signal == "SELL" and prev_signal == "BUY":
        return "STRONG_SELL"
    else:
        return current_signal

# Mock Binance data for development
MOCK_COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", 
    "XRPUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "LUNAUSDT"
]

def get_mock_coin_data() -> List[CoinData]:
    """Generate mock coin data for development"""
    import random
    coins = []
    
    for symbol in MOCK_COINS:
        # Generate mock price data
        base_price = random.uniform(0.1, 50000)
        change_24h = random.uniform(-15, 15)
        volume_24h = random.uniform(1000000, 100000000)
        
        # Generate mock EMA values
        ema9 = base_price * random.uniform(0.98, 1.02)
        ema21 = base_price * random.uniform(0.97, 1.03)
        
        # Generate signal
        signal = "BUY" if ema9 > ema21 else "SELL"
        
        coins.append(CoinData(
            symbol=symbol,
            price=round(base_price, 6),
            change_24h=round(change_24h, 2),
            volume_24h=round(volume_24h, 2),
            ema9=round(ema9, 6),
            ema21=round(ema21, 6),
            signal=signal
        ))
    
    return coins

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/register")
async def register(user: UserRegister):
    # Check if user exists
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user.password)
    
    new_user = {
        "user_id": user_id,
        "email": user.email,
        "name": user.name,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_admin": False,
        "api_key": None,
        "api_secret": None
    }
    
    users_collection.insert_one(new_user)
    
    # Create default subscription
    subscription = {
        "user_id": user_id,
        "is_active": False,
        "expires_at": None,
        "created_at": datetime.utcnow()
    }
    subscriptions_collection.insert_one(subscription)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "email": user.email,
            "name": user.name
        }
    }

@app.post("/api/login")
async def login(user: UserLogin):
    # Find user
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user["user_id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": db_user["user_id"],
            "email": db_user["email"],
            "name": db_user["name"]
        }
    }

@app.get("/api/user/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    subscription = subscriptions_collection.find_one({"user_id": current_user["user_id"]})
    
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "is_admin": current_user.get("is_admin", False),
        "has_api_key": bool(current_user.get("api_key")),
        "subscription": {
            "is_active": subscription.get("is_active", False) if subscription else False,
            "expires_at": subscription.get("expires_at") if subscription else None
        }
    }

@app.put("/api/user/api-key")
async def update_api_key(api_data: ApiKeyUpdate, current_user: dict = Depends(get_current_user)):
    # Update user's API keys (in production, these should be encrypted)
    users_collection.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "api_key": api_data.api_key,
            "api_secret": api_data.api_secret,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "API keys updated successfully"}

@app.get("/api/coins")
async def get_coins():
    """Get real-time coin data with EMA indicators"""
    try:
        # For development, return mock data
        coins_data = get_mock_coin_data()
        return {"coins": coins_data, "timestamp": datetime.utcnow()}
    
    except Exception as e:
        logger.error(f"Error fetching coin data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch coin data")

@app.get("/api/bot/config")
async def get_bot_config(current_user: dict = Depends(get_current_user)):
    config = bot_configs_collection.find_one({"user_id": current_user["user_id"]})
    
    if not config:
        # Return default config
        default_config = BotConfig()
        return default_config.dict()
    
    return {
        "symbol": config.get("symbol", "BTCUSDT"),
        "timeframe": config.get("timeframe", "1m"),
        "leverage": config.get("leverage", 1),
        "take_profit": config.get("take_profit", 2.0),
        "stop_loss": config.get("stop_loss", 1.0),
        "position_size": config.get("position_size", 10.0),
        "is_active": config.get("is_active", False)
    }

@app.put("/api/bot/config")
async def update_bot_config(config: BotConfig, current_user: dict = Depends(get_current_user)):
    bot_configs_collection.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            **config.dict(),
            "user_id": current_user["user_id"],
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    return {"message": "Bot configuration updated successfully"}

@app.post("/api/bot/start")
async def start_bot(current_user: dict = Depends(get_current_user)):
    # Check subscription
    subscription = subscriptions_collection.find_one({"user_id": current_user["user_id"]})
    if not subscription or not subscription.get("is_active"):
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    # Update bot status
    bot_configs_collection.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "is_active": True,
            "started_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    return {"message": "Bot started successfully"}

@app.post("/api/bot/stop")
async def stop_bot(current_user: dict = Depends(get_current_user)):
    bot_configs_collection.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "is_active": False,
            "stopped_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Bot stopped successfully"}

@app.get("/api/admin/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = list(users_collection.find({}, {"password": 0}))
    for user in users:
        subscription = subscriptions_collection.find_one({"user_id": user["user_id"]})
        user["subscription"] = subscription if subscription else {"is_active": False}
    
    return {"users": users}

@app.put("/api/admin/subscription/{user_id}")
async def update_subscription(user_id: str, days: int, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    expires_at = datetime.utcnow() + timedelta(days=days)
    
    subscriptions_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "is_active": True,
            "expires_at": expires_at,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    return {"message": f"Subscription updated for {days} days"}

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send real-time coin data every 5 seconds
            coins_data = get_mock_coin_data()
            await manager.send_personal_message(
                json.dumps({"type": "coins_update", "data": [coin.dict() for coin in coins_data]}),
                websocket
            )
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)