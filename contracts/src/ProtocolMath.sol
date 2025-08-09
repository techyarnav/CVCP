// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ProtocolMath
 * @dev Advanced mathematical library for CVCP credit score calculations
 * Implements sophisticated scoring algorithms with multiple behavioral components
 */
library ProtocolMath {
    // Protocol Constants
    uint256 public constant MAX_SCORE = 850;
    uint256 public constant MIN_SCORE = 300;
    uint256 public constant COMPONENT_MAX = 200;
    
    // Component Weights (totaling 100%)
    uint256 public constant TRANSACTION_WEIGHT = 25;
    uint256 public constant DEFI_WEIGHT = 20;
    uint256 public constant STAKING_WEIGHT = 25;
    uint256 public constant RISK_WEIGHT = 20;
    uint256 public constant HISTORY_WEIGHT = 10;
    
    /**
     * @dev BehavioralMetrics struct matching your DataProcessor output
     * Contains all 23 contract-ready metrics from your successful data pipeline
     */
    struct BehavioralMetrics {
        // Transaction Component (from Alchemy client)
        uint256 transactionFrequency;        // Monthly transaction count
        uint256 averageTransactionValue;     // Average USD value per transaction
        uint256 gasEfficiencyScore;          // Gas optimization score (0-100)
        uint256 crossChainActivityCount;     // Number of active chains
        uint256 consistencyMetric;           // Transaction consistency (0-100)
        
        // DeFi Component (from Zapper client)
        uint256 protocolInteractionCount;    // Unique protocols used
        uint256 totalDeFiBalanceUSD;         // Total DeFi portfolio value
        uint256 liquidityPositionCount;      // LP positions held
        uint256 protocolDiversityScore;      // Protocol diversification (0-100)
        
        // Staking Component (from Moralis client)
        uint256 totalStakedUSD;              // Total staking value
        uint256 stakingDurationDays;         // Average staking duration
        uint256 stakingPlatformCount;        // Unique staking platforms
        uint256 rewardClaimFrequency;        // Reward claiming frequency
        
        // Risk Component
        uint256 liquidationEventCount;       // Historical liquidations
        uint256 leverageRatio;               // Current leverage (100 = 1x)
        uint256 portfolioVolatility;         // Portfolio volatility score
        
        // Additional metrics for enhanced scoring
        uint256 stakingLoyaltyScore;         // Platform loyalty (0-100)
        uint256 interactionDepthScore;       // DeFi sophistication (0-100)
        uint256 yieldFarmingActive;          // Yield farming indicator (0/1)
        uint256 accountAgeScore;             // Account maturity score
        uint256 activityConsistencyScore;    // Overall activity consistency
        uint256 engagementScore;             // User engagement level
    }

    /**
     * @dev Calculate comprehensive transaction score
     * Weights: frequency(25%), volume(25%), gas(20%), chains(15%), consistency(15%)
     */
    function calculateTransactionScore(BehavioralMetrics memory metrics) 
        internal pure returns (uint256) {
        
        uint256 frequencyScore = logarithmicScale(metrics.transactionFrequency, 10);
        uint256 volumeScore = logarithmicScale(metrics.averageTransactionValue, 100);
        uint256 gasScore = normalizeToRange(metrics.gasEfficiencyScore, 0, 100, 50);
        uint256 crossChainScore = linearScale(metrics.crossChainActivityCount, 10, 50);
        uint256 consistencyScore = normalizeToRange(metrics.consistencyMetric, 0, 100, 50);
        
        uint256 totalScore = (
            frequencyScore * 25 +
            volumeScore * 25 +
            gasScore * 20 +
            crossChainScore * 15 +
            consistencyScore * 15
        ) / 100;
        
        return capToMax(totalScore, COMPONENT_MAX);
    }
    
    /**
     * @dev Calculate DeFi interaction score
     * Weights: protocols(35%), balance(25%), LP positions(25%), diversity(15%)
     */
    function calculateDeFiScore(BehavioralMetrics memory metrics) 
        internal pure returns (uint256) {
        
        uint256 protocolScore = linearScale(metrics.protocolInteractionCount, 15, 80);
        uint256 balanceScore = logarithmicScale(metrics.totalDeFiBalanceUSD, 1000);
        uint256 liquidityScore = linearScale(metrics.liquidityPositionCount, 8, 40);
        uint256 diversityScore = normalizeToRange(metrics.protocolDiversityScore, 0, 100, 30);
        
        // Sophistication bonus
        uint256 sophisticationBonus = metrics.interactionDepthScore / 10; // Max 10 bonus points
        uint256 yieldBonus = metrics.yieldFarmingActive * 5; // 5 points if yield farming
        
        uint256 totalScore = (
            protocolScore * 35 +
            balanceScore * 25 +
            liquidityScore * 25 +
            diversityScore * 15
        ) / 100;
        
        totalScore += sophisticationBonus + yieldBonus;
        
        return capToMax(totalScore, COMPONENT_MAX);
    }
    
    /**
     * @dev Calculate staking behavior score
     * Weights: amount(40%), duration(30%), platforms(20%), rewards(10%)
     */
    function calculateStakingScore(BehavioralMetrics memory metrics) 
        internal pure returns (uint256) {
        
        // Early return if there is effectively no staking activity
        if (
            metrics.totalStakedUSD == 0 &&
            metrics.stakingDurationDays == 0 &&
            metrics.stakingPlatformCount == 0
        ) {
            uint256 smallBonus = 0;
            if (metrics.stakingLoyaltyScore > 0) {
                smallBonus += metrics.stakingLoyaltyScore / 20; // up to 5
            }
            if (metrics.interactionDepthScore > 0) {
                smallBonus += metrics.interactionDepthScore / 50; // up to 2
            }
            return smallBonus;
        }
        
        uint256 amountScore = logarithmicScale(metrics.totalStakedUSD, 1000);
        uint256 durationScore = timeDecayFunction(metrics.stakingDurationDays);
        uint256 platformScore = linearScale(metrics.stakingPlatformCount, 6, 40);
        uint256 rewardScore = normalizeFrequency(metrics.rewardClaimFrequency, 20);
        
        // Loyalty bonus
        uint256 loyaltyBonus = metrics.stakingLoyaltyScore / 10; // Max 10 bonus points
        
        uint256 totalScore = (
            amountScore * 40 +
            durationScore * 30 +
            platformScore * 20 +
            rewardScore * 10
        ) / 100;
        
        totalScore += loyaltyBonus;
        
        return capToMax(totalScore, COMPONENT_MAX);
    }
    
    /**
     * @dev Calculate risk assessment score (higher is better)
     * Penalties applied for: liquidations, high leverage, volatility
     */
    function calculateRiskScore(BehavioralMetrics memory metrics) 
        internal pure returns (uint256) {
        
        uint256 baseScore = COMPONENT_MAX;
        
        // Liquidation penalty (30 points per liquidation)
        if (metrics.liquidationEventCount > 0) {
            uint256 liquidationPenalty = metrics.liquidationEventCount * 30;
            baseScore = baseScore > liquidationPenalty ? baseScore - liquidationPenalty : 0;
        }
        
        // Leverage penalty (starts at 2x leverage)
        if (metrics.leverageRatio > 200) {
            uint256 leveragePenalty = (metrics.leverageRatio - 200) / 10;
            baseScore = baseScore > leveragePenalty ? baseScore - leveragePenalty : 0;
        }
        
        // Volatility penalty (starts at 30% volatility)
        if (metrics.portfolioVolatility > 30) {
            uint256 volatilityPenalty = (metrics.portfolioVolatility - 30) * 2;
            baseScore = baseScore > volatilityPenalty ? baseScore - volatilityPenalty : 0;
        }
        
        return baseScore;
    }
    
    /**
     * @dev Calculate historical behavior score
     * Weights: activity(50%), commitment(30%), consistency(20%)
     */
    function calculateHistoryScore(BehavioralMetrics memory metrics) 
        internal pure returns (uint256) {
        
        uint256 activityScore = linearScale(metrics.transactionFrequency, 100, 80);
        uint256 commitmentScore = timeDecayFunction(metrics.stakingDurationDays);
        uint256 consistencyScore = normalizeToRange(metrics.consistencyMetric, 0, 100, 40);
        
        // Account age and engagement bonuses
        uint256 ageBonus = metrics.accountAgeScore / 10; // Max 10 bonus points
        uint256 engagementBonus = metrics.engagementScore / 20; // Max 5 bonus points
        uint256 activityConsistencyBonus = metrics.activityConsistencyScore / 20; // Max 5 bonus points
        
        uint256 totalScore = (
            activityScore * 50 +
            commitmentScore * 30 +
            consistencyScore * 20
        ) / 100;
        
        totalScore += ageBonus + engagementBonus + activityConsistencyBonus;
        
        return capToMax(totalScore, COMPONENT_MAX);
    }
    
    // ADVANCED MATHEMATICAL UTILITY FUNCTIONS
    
    /**
     * @dev Logarithmic scaling for values with diminishing returns
     */
    function logarithmicScale(uint256 value, uint256 base) internal pure returns (uint256) {
        if (value == 0) return 0;
        
        uint256 scaledValue = value + base;
        uint256 logValue = 0;
        
        while (scaledValue > 1) {
            scaledValue = scaledValue / 2;
            logValue++;
        }
        
        return logValue * 8; // Scale factor for appropriate range
    }
    
    /**
     * @dev Time decay function for staking duration
     * Models exponential growth that plateaus
     */
    function timeDecayFunction(uint256 durationDays) internal pure returns (uint256) {
        if (durationDays == 0) return 0;
        if (durationDays >= 365) return 100;
        
        // Exponential approximation: score = 100 * (1 - e^(-t/30))
        return (durationDays * 100) / (durationDays + 30);
    }
    
    /**
     * @dev Linear scaling with maximum bounds
     */
    function linearScale(uint256 value, uint256 maxInput, uint256 maxOutput) 
        internal pure returns (uint256) {
        if (value >= maxInput) return maxOutput;
        return (value * maxOutput) / maxInput;
    }
    
    /**
     * @dev Normalize values to a specific range
     */
    function normalizeToRange(uint256 value, uint256 minInput, uint256 maxInput, uint256 maxOutput) 
        internal pure returns (uint256) {
        if (value <= minInput) return 0;
        if (value >= maxInput) return maxOutput;
        
        return ((value - minInput) * maxOutput) / (maxInput - minInput);
    }
    
    /**
     * @dev Bell curve scoring for frequency metrics
     * Optimal frequency gets maximum score
     */
    function normalizeFrequency(uint256 frequency, uint256 optimalFreq) 
        internal pure returns (uint256) {
        if (frequency == 0) return 0;
        
        uint256 deviation = frequency > optimalFreq 
            ? frequency - optimalFreq 
            : optimalFreq - frequency;
            
        if (deviation > optimalFreq) return 0;
        
        return 100 - ((deviation * 100) / optimalFreq);
    }
    
    /**
     * @dev Cap values to maximum allowed
     */
    function capToMax(uint256 value, uint256 maxValue) internal pure returns (uint256) {
        return value > maxValue ? maxValue : value;
    }
    
    /**
     * @dev Protocol invariant: Ensure score components are within bounds
     */
    function validateComponentScore(uint256 score) internal pure returns (bool) {
        return score <= COMPONENT_MAX;
    }
    
    /**
     * @dev Protocol invariant: Ensure final score is within valid range
     */
    function validateFinalScore(uint256 score) internal pure returns (bool) {
        return score >= MIN_SCORE && score <= MAX_SCORE;
    }
}
