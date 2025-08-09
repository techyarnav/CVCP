# backend/run_tests.py
#!/usr/bin/env python3
"""Simple test runner for CVCP Step 1"""

import asyncio
import os

async def quick_test():
    """Quick test of core functionality"""
    
    print("🧪 CVCP Step 1 - Quick Test")
    print("=" * 40)
    
    # Test individual components
    try:
        # Test environment
        required_keys = ['ALCHEMY_API_KEY', 'ZAPPER_API_KEY', 'MORALIS_API_KEY']
        missing = [k for k in required_keys if not os.getenv(k)]
        
        if missing:
            print(f"⚠️ Missing API keys: {', '.join(missing)}")
        else:
            print("✅ All API keys configured")
        
        # Test imports
        from clients.multi_chain_aggregator import MultiChainDataAggregator
        print("✅ All imports successful")
        
        # Quick aggregator test
        aggregator = MultiChainDataAggregator()
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        
        print(f"🔄 Testing with address: {test_address}")
        result = await aggregator.fetch_user_comprehensive_data(test_address)
        
        print(f"✅ Data collection completed")
        print(f"📊 Quality grade: {result.get('data_quality_analysis', {}).get('quality_grade', 'Unknown')}")
        print(f"📈 User category: {result.get('user_analytics', {}).get('user_category', 'Unknown')}")
        
        print("\n🎉 Quick test PASSED! Ready for full testing.")
        
    except Exception as e:
        print(f"❌ Quick test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())
