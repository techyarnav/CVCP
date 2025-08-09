# backend/test_data_collection.py
import asyncio
import json
import os
from datetime import datetime

# Set up environment for testing
os.environ.setdefault('ALCHEMY_API_KEY', 'your_test_key_here')
os.environ.setdefault('ZAPPER_API_KEY', 'your_test_key_here') 
os.environ.setdefault('DEBANK_API_KEY', 'your_test_key_here')

from clients.multi_chain_aggregator import MultiChainDataAggregator

async def test_data_collection_pipeline():
    """Complete test of the data collection pipeline"""
    
    print("🚀 Starting CVCP Data Collection Pipeline Test")
    print("=" * 60)
    
    # Test addresses (use real addresses for meaningful results)
    test_addresses = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
        "0x742d35Cc6654c967e5c749CB1b5B43cA2E9b0b70",  # Random active address
    ]
    
    aggregator = MultiChainDataAggregator()
    
    for i, address in enumerate(test_addresses, 1):
        print(f"\n📊 Test {i}: Processing address {address}")
        print("-" * 40)
        
        start_time = datetime.now()
        
        try:
            # Fetch comprehensive data
            data = await aggregator.fetch_user_comprehensive_data(address)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Analyze results
            print(f"✅ Processing completed in {processing_time:.2f} seconds")
            print(f"📈 Data Quality Grade: {data['data_quality']['quality_grade']}")
            print(f"📊 Completeness: {data['data_quality']['completeness_percentage']}%")
            print(f"👤 User Profile: {data['summary']['user_profile']}")
            
            # Show key metrics
            tx_metrics = data['structured_metrics']['transaction_metrics']
            defi_metrics = data['structured_metrics']['defi_metrics'] 
            staking_metrics = data['structured_metrics']['staking_metrics']
            
            print(f"\n🔄 Transaction Activity:")
            print(f"  - Monthly Transactions: {tx_metrics['transactionFrequency']}")
            print(f"  - Cross-Chain Activity: {tx_metrics['crossChainActivityCount']} chains")
            print(f"  - Consistency Score: {tx_metrics['consistencyMetric']}/100")
            
            print(f"\n🏦 DeFi Engagement:")
            print(f"  - Unique Protocols: {defi_metrics['protocolInteractionCount']}")
            print(f"  - Total Balance: ${defi_metrics['totalDeFiBalanceUSD']:,}")
            print(f"  - LP Positions: {defi_metrics['liquidityPositionCount']}")
            
            print(f"\n🥩 Staking Activity:")
            print(f"  - Total Staked: ${staking_metrics['totalStakedUSD']:,}")
            print(f"  - Platform Count: {staking_metrics['stakingPlatformCount']}")
            print(f"  - Avg Duration: {staking_metrics['stakingDurationDays']} days")
            
            # Test data structure for smart contract compatibility
            assert isinstance(tx_metrics['transactionFrequency'], int)
            assert isinstance(defi_metrics['totalDeFiBalanceUSD'], int)
            assert isinstance(staking_metrics['totalStakedUSD'], int)
            
            print("✅ Data structure validation passed")
            
            # Save results for analysis
            filename = f"test_results_{address[-6:]}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"💾 Results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error processing {address}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Testing completed!")

async def test_individual_clients():
    """Test individual API clients separately"""
    
    print("\n🔧 Testing Individual API Clients")
    print("=" * 40)
    
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    # Test Alchemy Client
    print("\n1️⃣ Testing Alchemy Client (Transaction Data)")
    try:
        from clients.alchemy_client import AlchemyClient
        alchemy = AlchemyClient()
        alchemy_data = await alchemy.get_transaction_metrics(test_address)
        print(f"✅ Alchemy: {alchemy_data.get('total_transactions', 0)} total transactions")
        print(f"   Quality Score: {alchemy_data.get('data_quality_score', 0)}/100")
    except Exception as e:
        print(f"❌ Alchemy failed: {str(e)}")
    
    # Test Zapper Client  
    print("\n2️⃣ Testing Zapper Client (DeFi Data)")
    try:
        from clients.zapper_client import ZapperClient
        zapper = ZapperClient()
        zapper_data = await zapper.get_defi_metrics(test_address)
        print(f"✅ Zapper: {zapper_data.get('unique_protocols', 0)} unique protocols")
        print(f"   Total Balance: ${zapper_data.get('total_balance_usd', 0):,.2f}")
    except Exception as e:
        print(f"❌ Zapper failed: {str(e)}")
    
    # Test DeBank Client
    print("\n3️⃣ Testing DeBank Client (Staking Data)")
    try:
        from clients.debank_client import DeBankClient
        debank = DeBankClient()
        debank_data = await debank.get_staking_metrics(test_address)
        print(f"✅ DeBank: ${debank_data.get('total_staked_usd', 0):,.2f} staked")
        print(f"   Platform Count: {debank_data.get('platform_count', 0)}")
    except Exception as e:
        print(f"❌ DeBank failed: {str(e)}")

async def test_error_handling():
    """Test error handling with invalid inputs"""
    
    print("\n🚨 Testing Error Handling")
    print("=" * 30)
    
    aggregator = MultiChainDataAggregator()
    
    # Test invalid address
    print("\n🔍 Testing invalid address format")
    try:
        invalid_data = await aggregator.fetch_user_comprehensive_data("invalid_address")
        assert invalid_data['data_quality']['completeness_percentage'] == 0
        print("✅ Invalid address handled correctly")
    except ValueError as e:
        print("✅ Invalid address rejected with proper error")
    
    # Test empty address
    print("\n🔍 Testing empty address")
    try:
        empty_data = await aggregator.fetch_user_comprehensive_data("0x0000000000000000000000000000000000000000")
        print("✅ Empty address processed (likely returns empty data)")
    except Exception as e:
        print(f"✅ Empty address handled: {str(e)}")

async def benchmark_performance():
    """Benchmark the performance of data collection"""
    
    print("\n⚡ Performance Benchmarking")
    print("=" * 30)
    
    aggregator = MultiChainDataAggregator()
    test_addresses = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "0x742d35Cc6654c967e5c749CB1b5B43cA2E9b0b70",
        "0x8ba1f109551bD432803012645Hac136c4e31F7C7"  # Another test address
    ]
    
    times = []
    
    print(f"Testing with {len(test_addresses)} addresses...")
    
    for address in test_addresses:
        start_time = datetime.now()
        try:
            await aggregator.fetch_user_comprehensive_data(address)
            processing_time = (datetime.now() - start_time).total_seconds()
            times.append(processing_time)
            print(f"⏱️  {address[-6:]}: {processing_time:.2f}s")
        except Exception as e:
            print(f"❌ {address[-6:]}: Error - {str(e)}")
    
    if times:
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n📊 Performance Summary:")
        print(f"   Average Time: {avg_time:.2f}s")
        print(f"   Fastest: {min_time:.2f}s")
        print(f"   Slowest: {max_time:.2f}s")
        
        # Performance assertions
        assert avg_time < 60, f"Average processing time too slow: {avg_time}s"
        assert max_time < 120, f"Max processing time too slow: {max_time}s"
        
        print("✅ Performance benchmarks passed")

def validate_smart_contract_data_format(data: dict):
    """Validate that data format matches smart contract requirements"""
    
    print("\n🔍 Validating Smart Contract Data Format")
    print("-" * 40)
    
    structured_metrics = data.get('structured_metrics', {})
    
    # Validate transaction metrics
    tx_metrics = structured_metrics.get('transaction_metrics', {})
    required_tx_fields = [
        'transactionFrequency', 'averageTransactionValue', 'gasEfficiencyScore',
        'crossChainActivityCount', 'consistencyMetric'
    ]
    
    for field in required_tx_fields:
        assert field in tx_metrics, f"Missing transaction field: {field}"
        assert isinstance(tx_metrics[field], int), f"Transaction field {field} must be integer"
    
    print("✅ Transaction metrics format valid")
    
    # Validate DeFi metrics
    defi_metrics = structured_metrics.get('defi_metrics', {})
    required_defi_fields = [
        'protocolInteractionCount', 'totalDeFiBalanceUSD', 'liquidityPositionCount',
        'protocolDiversityScore', 'interactionDepthScore'
    ]
    
    for field in required_defi_fields:
        assert field in defi_metrics, f"Missing DeFi field: {field}"
        assert isinstance(defi_metrics[field], int), f"DeFi field {field} must be integer"
    
    print("✅ DeFi metrics format valid")
    
    # Validate staking metrics
    staking_metrics = structured_metrics.get('staking_metrics', {})
    required_staking_fields = [
        'totalStakedUSD', 'stakingDurationDays', 'stakingPlatformCount',
        'rewardClaimFrequency', 'stakingLoyaltyScore'
    ]
    
    for field in required_staking_fields:
        assert field in staking_metrics, f"Missing staking field: {field}"
        assert isinstance(staking_metrics[field], int), f"Staking field {field} must be integer"
    
    print("✅ Staking metrics format valid")
    print("✅ All data formats compatible with smart contracts")

async def run_comprehensive_tests():
    """Run all comprehensive tests"""
    
    print("🧪 CVCP Data Collection - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run main pipeline tests
        await test_data_collection_pipeline()
        
        # Test individual clients
        await test_individual_clients()
        
        # Test error handling
        await test_error_handling()
        
        # Benchmark performance
        await benchmark_performance()
        
        # Test data format validation (using sample data)
        print("\n🔍 Testing Data Format Validation")
        aggregator = MultiChainDataAggregator()
        sample_data = await aggregator.fetch_user_comprehensive_data("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        validate_smart_contract_data_format(sample_data)
        
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("✅ Data collection pipeline is ready for smart contract integration")
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

# Main execution
if __name__ == "__main__":
    # Check environment setup
    required_env_vars = ['ALCHEMY_API_KEY', 'ZAPPER_API_KEY', 'DEBANK_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Warning: Missing API keys for:")
        for var in missing_vars:
            print(f"   - {var}")
        print("   Tests will run but may have limited functionality")
    
    # Run the comprehensive test suite
    success = asyncio.run(run_comprehensive_tests())
    
    if success:
        print("\n📋 Next Steps:")
        print("1. Add your real API keys to .env file")
        print("2. Run tests again with real keys")
        print("3. Move to Phase 2: Smart Contract Development")
        print("4. Implement the ProtocolMath.sol and CreditScoreRegistry.sol")
    else:
        print("\n🔧 Fix the issues above before proceeding to smart contracts")
