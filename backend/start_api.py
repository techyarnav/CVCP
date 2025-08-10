# backend/start_api.py

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if environment is properly configured"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔧 Checking environment configuration...")
    
    required_vars = {
        'PRIVATE_KEY': 'Wallet private key for contract interactions',
        'DEPLOYED_REGISTRY_ADDRESS': 'Deployed contract address',
        'RPC_URL': 'Blockchain RPC endpoint'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * 10}...{value[-4:]}")
        else:
            print(f"   ❌ {var}: Missing ({description})")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nTo fix this:")
        print("1. Make sure your .env file exists in the backend directory")
        print("2. Add the missing variables to your .env file")
        print("3. For testing, you can use the deployed contract values:")
        print(f"   DEPLOYED_REGISTRY_ADDRESS=0x8e9288aD536Ee22Df91026BE96cB1deE904C05eF")
        print(f"   RPC_URL=https://scroll-sepolia.g.alchemy.com/v2/FKj-Ao97HOyiDsdSHZ3ED")
        print(f"   PRIVATE_KEY=<your_wallet_private_key>")
        print("\n❌ Cannot start API without proper configuration")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

def start_api():
    """Start the API server"""
    
    if not check_environment():
        sys.exit(1)
    
    print("\n🚀 Starting Credit Score API...")
    
    # Import and run the API
    try:
        import uvicorn
        from api.credit_score_api import app
        
        print("✅ API modules imported successfully")
        print("🌐 Starting server at http://localhost:8000")
        print("📚 API documentation available at http://localhost:8000/docs")
        print("🔗 Health check at http://localhost:8000/health")
        
        uvicorn.run(
            "api.credit_score_api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Failed to start API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_api()