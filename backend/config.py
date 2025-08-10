# backend/config.py

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the API"""
    
    def __init__(self):
        # Smart Contract Configuration
        self.CONTRACT_ADDRESS = os.getenv("DEPLOYED_REGISTRY_ADDRESS", "0x8e9288aD536Ee22Df91026BE96cB1deE904C05eF")
        self.RPC_URL = os.getenv("RPC_URL", "https://scroll-sepolia.g.alchemy.com/v2/FKj-Ao97HOyiDsdSHZ3ED")
        self.PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
        self.CHAIN_ID = int(os.getenv("CHAIN_ID", "534351"))
        
        # API Configuration
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT = int(os.getenv("API_PORT", "8000"))
        self.API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"
        
        # Data Provider API Keys
        self.ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY", "")
        self.ZAPPER_API_KEY = os.getenv("ZAPPER_API_KEY", "")
        self.MORALIS_API_KEY = os.getenv("MORALIS_API_KEY", "")
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
        
        # Cache Configuration
        self.CACHE_DURATION_MINUTES = int(os.getenv("CACHE_DURATION_MINUTES", "30"))
        
        # CORS Configuration
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    def validate(self) -> bool:
        """Validate required configuration"""
        required_fields = [
            ("CONTRACT_ADDRESS", self.CONTRACT_ADDRESS),
            ("RPC_URL", self.RPC_URL),
            ("PRIVATE_KEY", self.PRIVATE_KEY)
        ]
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value:
                missing_fields.append(field_name)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True

# Global config instance
config = Config()