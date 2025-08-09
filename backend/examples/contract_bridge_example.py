# backend/examples/contract_bridge_example.py

import asyncio
import os
from services.contract_bridge import ContractBridge, convert_dataprocessor_to_metrics

async def main():
    """Example usage of ContractBridge"""
    
    # Example DataProcessor output (matching your successful implementation)
    dataprocessor_output = {
        'transactionFrequency': 25,
        'averageTransactionValue': 500,
        'gasEfficiencyScore': 75,
        'crossChainActivityCount': 3,
        'consistencyMetric': 80,
        'protocolInteractionCount': 5,
        'totalDeFiBalanceUSD': 10000,
        'liquidityPositionCount': 2,
        'protocolDiversityScore': 60,
        'totalStakedUSD': 5000,
        'stakingDurationDays': 180,
        'stakingPlatformCount': 2,
        'rewardClaimFrequency': 8,
        'liquidationEventCount': 0,
        'leverageRatio': 100,
        'portfolioVolatility': 25,
        'stakingLoyaltyScore': 65,
        'interactionDepthScore': 70,
        'yieldFarmingActive': 1,
        'accountAgeScore': 75,
        'activityConsistencyScore': 80,
        'engagementScore': 85
    }
    
    # Convert to contract format
    metrics = convert_dataprocessor_to_metrics(dataprocessor_output)
    
    try:
        # Initialize contract bridge
        bridge = ContractBridge()
        
        # Get contract info
        info = bridge.get_contract_info()
        print(f"Contract Info: {info}")
        
        # Preview score (no transaction cost)
        preview_score, confidence = await bridge.preview_score(metrics)
        print(f"Preview Score: {preview_score} (confidence: {confidence}%)")
        
        # Example user address
        user_address = "0x742d35Cc6654c967e5c749CB1b5B43cA2E9b0b70"
        
        # Complete flow: Update data and calculate score
        result = await bridge.process_user_complete_flow(user_address, metrics)
        
        print("Complete Flow Result:")
        print(f"- User: {result['user_address']}")
        print(f"- Update TX: {result['update_transaction']}")
        print(f"- Calculation TX: {result['calculation_transaction']}")
        print(f"- Final Score: {result['credit_score']['total_score']}")
        print(f"- Confidence: {result['credit_score']['confidence']}%")
        print(f"- Component Scores:")
        print(f"  - Transaction: {result['credit_score']['transaction_score']}")
        print(f"  - DeFi: {result['credit_score']['defi_score']}")
        print(f"  - Staking: {result['credit_score']['staking_score']}")
        print(f"  - Risk: {result['credit_score']['risk_score']}")
        print(f"  - History: {result['credit_score']['history_score']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
