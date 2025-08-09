// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/ProtocolMath.sol";

contract ProtocolMathTest is Test {
    using ProtocolMath for ProtocolMath.BehavioralMetrics;
    
    // Test fixtures
    ProtocolMath.BehavioralMetrics internal defaultMetrics;
    ProtocolMath.BehavioralMetrics internal highActivityMetrics;
    ProtocolMath.BehavioralMetrics internal lowActivityMetrics;
    ProtocolMath.BehavioralMetrics internal riskMetrics;
    
    function setUp() public {
        // Default balanced user metrics
        defaultMetrics = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 25,
            averageTransactionValue: 500,
            gasEfficiencyScore: 75,
            crossChainActivityCount: 3,
            consistencyMetric: 80,
            protocolInteractionCount: 5,
            totalDeFiBalanceUSD: 10000,
            liquidityPositionCount: 2,
            protocolDiversityScore: 60,
            totalStakedUSD: 5000,
            stakingDurationDays: 180,
            stakingPlatformCount: 2,
            rewardClaimFrequency: 8,
            liquidationEventCount: 0,
            leverageRatio: 100, // 1x
            portfolioVolatility: 25,
            stakingLoyaltyScore: 65,
            interactionDepthScore: 70,
            yieldFarmingActive: 1,
            accountAgeScore: 75,
            activityConsistencyScore: 80,
            engagementScore: 85
        });
        
        // High activity whale user
        highActivityMetrics = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 100,
            averageTransactionValue: 5000,
            gasEfficiencyScore: 90,
            crossChainActivityCount: 10,
            consistencyMetric: 95,
            protocolInteractionCount: 15,
            totalDeFiBalanceUSD: 100000,
            liquidityPositionCount: 8,
            protocolDiversityScore: 90,
            totalStakedUSD: 50000,
            stakingDurationDays: 365,
            stakingPlatformCount: 6,
            rewardClaimFrequency: 20,
            liquidationEventCount: 0,
            leverageRatio: 100,
            portfolioVolatility: 15,
            stakingLoyaltyScore: 90,
            interactionDepthScore: 95,
            yieldFarmingActive: 1,
            accountAgeScore: 95,
            activityConsistencyScore: 90,
            engagementScore: 95
        });
        
        // Low activity newcomer
        lowActivityMetrics = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 2,
            averageTransactionValue: 50,
            gasEfficiencyScore: 50,
            crossChainActivityCount: 1,
            consistencyMetric: 30,
            protocolInteractionCount: 0,
            totalDeFiBalanceUSD: 100,
            liquidityPositionCount: 0,
            protocolDiversityScore: 0,
            totalStakedUSD: 0,
            stakingDurationDays: 0,
            stakingPlatformCount: 0,
            rewardClaimFrequency: 0,
            liquidationEventCount: 0,
            leverageRatio: 100,
            portfolioVolatility: 50,
            stakingLoyaltyScore: 10,
            interactionDepthScore: 5,
            yieldFarmingActive: 0,
            accountAgeScore: 20,
            activityConsistencyScore: 25,
            engagementScore: 15
        });
        
        // High risk user
        riskMetrics = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 50,
            averageTransactionValue: 1000,
            gasEfficiencyScore: 60,
            crossChainActivityCount: 2,
            consistencyMetric: 40,
            protocolInteractionCount: 8,
            totalDeFiBalanceUSD: 20000,
            liquidityPositionCount: 5,
            protocolDiversityScore: 50,
            totalStakedUSD: 2000,
            stakingDurationDays: 30,
            stakingPlatformCount: 1,
            rewardClaimFrequency: 5,
            liquidationEventCount: 2, // High risk: 2 liquidations
            leverageRatio: 500, // High risk: 5x leverage
            portfolioVolatility: 80, // High volatility
            stakingLoyaltyScore: 30,
            interactionDepthScore: 40,
            yieldFarmingActive: 1,
            accountAgeScore: 60,
            activityConsistencyScore: 45,
            engagementScore: 50
        });
    }
    
    // COMPONENT SCORE TESTS
    
    function testCalculateTransactionScore() public {
        uint256 score = ProtocolMath.calculateTransactionScore(defaultMetrics);
        
        // Should be within component bounds
        assertGt(score, 0, "Transaction score should be positive");
        assertLe(score, ProtocolMath.COMPONENT_MAX, "Transaction score exceeds maximum");
        
        // High activity should score higher
        uint256 highScore = ProtocolMath.calculateTransactionScore(highActivityMetrics);
        uint256 lowScore = ProtocolMath.calculateTransactionScore(lowActivityMetrics);
        
        assertGt(highScore, score, "High activity should score higher than default");
        assertGt(score, lowScore, "Default should score higher than low activity");
        
        emit log_named_uint("Transaction Score High", highScore);
        emit log_named_uint("Transaction Score Default", score);
        emit log_named_uint("Transaction Score Low", lowScore);
    }
    
    function testCalculateDeFiScore() public {
        uint256 score = ProtocolMath.calculateDeFiScore(defaultMetrics);
        
        assertGt(score, 0, "DeFi score should be positive");
        assertLe(score, ProtocolMath.COMPONENT_MAX, "DeFi score exceeds maximum");
        
        // Test with no DeFi activity
        uint256 lowScore = ProtocolMath.calculateDeFiScore(lowActivityMetrics);
        assertLt(lowScore, score, "No DeFi activity should score lower");
        
        // Test with high DeFi activity
        uint256 highScore = ProtocolMath.calculateDeFiScore(highActivityMetrics);
        assertGt(highScore, score, "High DeFi activity should score higher");
        
        emit log_named_uint("DeFi Score High", highScore);
        emit log_named_uint("DeFi Score Default", score);
        emit log_named_uint("DeFi Score Low", lowScore);
    }
    
    function testCalculateStakingScore() public {
        uint256 score = ProtocolMath.calculateStakingScore(defaultMetrics);
        
        assertGt(score, 0, "Staking score should be positive");
        assertLe(score, ProtocolMath.COMPONENT_MAX, "Staking score exceeds maximum");
        
        // Test with no staking - allow small non-zero due to bonuses
        uint256 lowScore = ProtocolMath.calculateStakingScore(lowActivityMetrics);
        assertLe(lowScore, 10, "No staking should result in very low score");
        
        // Test with high staking
        uint256 highScore = ProtocolMath.calculateStakingScore(highActivityMetrics);
        assertGt(highScore, score, "High staking should score higher");
        
        emit log_named_uint("Staking Score High", highScore);
        emit log_named_uint("Staking Score Default", score);
        emit log_named_uint("Staking Score Low", lowScore);
    }
    
    function testCalculateRiskScore() public {
        uint256 defaultRiskScore = ProtocolMath.calculateRiskScore(defaultMetrics);
        uint256 highRiskScore = ProtocolMath.calculateRiskScore(riskMetrics);
        
        // Risk score should be within bounds
        assertLe(defaultRiskScore, ProtocolMath.COMPONENT_MAX, "Default risk score exceeds maximum");
        assertLe(highRiskScore, ProtocolMath.COMPONENT_MAX, "High risk score exceeds maximum");
        
        // High risk should score lower (risk score is inverse - higher is better)
        assertGt(defaultRiskScore, highRiskScore, "High risk should score lower than default");
        
        // Test liquidation penalty
        assertLt(highRiskScore, defaultRiskScore, "Liquidations should reduce risk score");
        
        emit log_named_uint("Risk Score Default", defaultRiskScore);
        emit log_named_uint("Risk Score HighRisk", highRiskScore);
    }
    
    function testCalculateHistoryScore() public {
        uint256 score = ProtocolMath.calculateHistoryScore(defaultMetrics);
        
        assertGt(score, 0, "History score should be positive");
        assertLe(score, ProtocolMath.COMPONENT_MAX, "History score exceeds maximum");
        
        uint256 highScore = ProtocolMath.calculateHistoryScore(highActivityMetrics);
        uint256 lowScore = ProtocolMath.calculateHistoryScore(lowActivityMetrics);
        
        assertGt(highScore, score, "High activity history should score higher");
        assertGt(score, lowScore, "Default should score higher than low activity");
        
        emit log_named_uint("History Score High", highScore);
        emit log_named_uint("History Score Default", score);
        emit log_named_uint("History Score Low", lowScore);
    }
    
    // MATHEMATICAL UTILITY FUNCTION TESTS
    
    function testLogarithmicScale() public {
        // Test zero input
        uint256 zeroResult = ProtocolMath.logarithmicScale(0, 10);
        assertEq(zeroResult, 0, "Zero input should return zero");
        
        // Test monotonicity
        uint256 small = ProtocolMath.logarithmicScale(10, 10);
        uint256 medium = ProtocolMath.logarithmicScale(100, 10);
        uint256 large = ProtocolMath.logarithmicScale(1000, 10);
        
        assertGt(medium, small, "Logarithmic scale should be monotonic");
        assertGt(large, medium, "Logarithmic scale should be monotonic");
        
        emit log_named_uint("LogarithmicScale(10)", small);
        emit log_named_uint("LogarithmicScale(100)", medium);
        emit log_named_uint("LogarithmicScale(1000)", large);
    }
    
    function testTimeDecayFunction() public {
        // Test zero duration
        uint256 zero = ProtocolMath.timeDecayFunction(0);
        assertEq(zero, 0, "Zero duration should return zero");
        
        // Test maximum duration
        uint256 max = ProtocolMath.timeDecayFunction(365);
        assertEq(max, 100, "365 days should return maximum score");
        
        // Test monotonicity
        uint256 short = ProtocolMath.timeDecayFunction(30);
        uint256 medium = ProtocolMath.timeDecayFunction(90);
        uint256 long = ProtocolMath.timeDecayFunction(180);
        
        assertGt(medium, short, "Time decay should be monotonic");
        assertGt(long, medium, "Time decay should be monotonic");
        assertLt(long, max, "Long duration should be less than maximum");
        
        emit log_named_uint("TimeDecay(30d)", short);
        emit log_named_uint("TimeDecay(90d)", medium);
        emit log_named_uint("TimeDecay(180d)", long);
        emit log_named_uint("TimeDecay(365d)", max);
    }
    
    function testLinearScale() public {
        // Test boundary conditions
        uint256 zero = ProtocolMath.linearScale(0, 100, 50);
        assertEq(zero, 0, "Zero input should return zero");
        
        uint256 max = ProtocolMath.linearScale(100, 100, 50);
        assertEq(max, 50, "Maximum input should return maximum output");
        
        uint256 over = ProtocolMath.linearScale(200, 100, 50);
        assertEq(over, 50, "Over maximum should be capped");
        
        // Test midpoint
        uint256 mid = ProtocolMath.linearScale(50, 100, 50);
        assertEq(mid, 25, "Midpoint should be half of maximum");
        
        emit log_named_uint("LinearScale(0)", zero);
        emit log_named_uint("LinearScale(50)", mid);
        emit log_named_uint("LinearScale(100)", max);
        emit log_named_uint("LinearScale(200)", over);
    }
    
    function testNormalizeToRange() public {
        // Test boundary conditions
        uint256 min = ProtocolMath.normalizeToRange(10, 10, 100, 50);
        assertEq(min, 0, "Minimum input should return zero");
        
        uint256 max = ProtocolMath.normalizeToRange(100, 10, 100, 50);
        assertEq(max, 50, "Maximum input should return maximum output");
        
        uint256 mid = ProtocolMath.normalizeToRange(55, 10, 100, 50);
        assertEq(mid, 25, "Midpoint should be half of maximum");
        
        emit log_named_uint("NormalizeToRange(Min)", min);
        emit log_named_uint("NormalizeToRange(Mid)", mid);
        emit log_named_uint("NormalizeToRange(Max)", max);
    }
    
    function testNormalizeFrequency() public {
        uint256 optimal = ProtocolMath.normalizeFrequency(20, 20);
        assertEq(optimal, 100, "Optimal frequency should return 100");
        
        uint256 half = ProtocolMath.normalizeFrequency(10, 20);
        assertEq(half, 50, "Half optimal should return 50");
        
        uint256 zero = ProtocolMath.normalizeFrequency(0, 20);
        assertEq(zero, 0, "Zero frequency should return 0");
        
        uint256 excessive = ProtocolMath.normalizeFrequency(50, 20);
        assertEq(excessive, 0, "Excessive frequency should return 0");
        
        emit log_named_uint("NormalizeFrequency(Optimal)", optimal);
        emit log_named_uint("NormalizeFrequency(Half)", half);
        emit log_named_uint("NormalizeFrequency(Excessive)", excessive);
    }
    
    // INVARIANT TESTS
    
    function testComponentScoreInvariants() public {
        uint256 txScore = ProtocolMath.calculateTransactionScore(defaultMetrics);
        uint256 defiScore = ProtocolMath.calculateDeFiScore(defaultMetrics);
        uint256 stakingScore = ProtocolMath.calculateStakingScore(defaultMetrics);
        uint256 riskScore = ProtocolMath.calculateRiskScore(defaultMetrics);
        uint256 historyScore = ProtocolMath.calculateHistoryScore(defaultMetrics);
        
        // All component scores must be within bounds
        assertTrue(ProtocolMath.validateComponentScore(txScore), "Transaction score invalid");
        assertTrue(ProtocolMath.validateComponentScore(defiScore), "DeFi score invalid");
        assertTrue(ProtocolMath.validateComponentScore(stakingScore), "Staking score invalid");
        assertTrue(ProtocolMath.validateComponentScore(riskScore), "Risk score invalid");
        assertTrue(ProtocolMath.validateComponentScore(historyScore), "History score invalid");
        
        emit log_named_uint("Component Score TX", txScore);
        emit log_named_uint("Component Score DeFi", defiScore);
        emit log_named_uint("Component Score Staking", stakingScore);
        emit log_named_uint("Component Score Risk", riskScore);
        emit log_named_uint("Component Score History", historyScore);
    }
    
    function testScoreMonotonicity() public {
        // Test that better metrics lead to better scores
        uint256 lowTxScore = ProtocolMath.calculateTransactionScore(lowActivityMetrics);
        uint256 defaultTxScore = ProtocolMath.calculateTransactionScore(defaultMetrics);
        uint256 highTxScore = ProtocolMath.calculateTransactionScore(highActivityMetrics);
        
        assertLe(lowTxScore, defaultTxScore, "Low activity should score <= default");
        assertLe(defaultTxScore, highTxScore, "Default should score <= high activity");
        
        // Test DeFi monotonicity
        uint256 lowDefiScore = ProtocolMath.calculateDeFiScore(lowActivityMetrics);
        uint256 defaultDefiScore = ProtocolMath.calculateDeFiScore(defaultMetrics);
        uint256 highDefiScore = ProtocolMath.calculateDeFiScore(highActivityMetrics);
        
        assertLe(lowDefiScore, defaultDefiScore, "Low DeFi activity should score <= default");
        assertLe(defaultDefiScore, highDefiScore, "Default DeFi should score <= high activity");
    }
    
    // FUZZ TESTS
    
    function testFuzzTransactionScore(uint256 frequency, uint256 value, uint256 gasScore, uint256 chains, uint256 consistency) public {
        // Bound inputs to realistic ranges
        frequency = bound(frequency, 0, 1000);
        value = bound(value, 0, 1000000);
        gasScore = bound(gasScore, 0, 100);
        chains = bound(chains, 0, 20);
        consistency = bound(consistency, 0, 100);
        
        ProtocolMath.BehavioralMetrics memory fuzzMetrics = defaultMetrics;
        fuzzMetrics.transactionFrequency = frequency;
        fuzzMetrics.averageTransactionValue = value;
        fuzzMetrics.gasEfficiencyScore = gasScore;
        fuzzMetrics.crossChainActivityCount = chains;
        fuzzMetrics.consistencyMetric = consistency;
        
        uint256 score = ProtocolMath.calculateTransactionScore(fuzzMetrics);
        
        // Invariant: score must be within bounds
        assertLe(score, ProtocolMath.COMPONENT_MAX, "Fuzz transaction score exceeds maximum");
        assertTrue(ProtocolMath.validateComponentScore(score), "Fuzz transaction score invalid");
    }
    
    function testFuzzRiskScore(uint256 liquidations, uint256 leverage, uint256 volatility) public {
        // Bound inputs to realistic ranges
        liquidations = bound(liquidations, 0, 10);
        leverage = bound(leverage, 100, 2000); // 1x to 20x
        volatility = bound(volatility, 0, 100);
        
        ProtocolMath.BehavioralMetrics memory fuzzMetrics = defaultMetrics;
        fuzzMetrics.liquidationEventCount = liquidations;
        fuzzMetrics.leverageRatio = leverage;
        fuzzMetrics.portfolioVolatility = volatility;
        
        uint256 score = ProtocolMath.calculateRiskScore(fuzzMetrics);
        
        // Invariant: score must be within bounds
        assertLe(score, ProtocolMath.COMPONENT_MAX, "Fuzz risk score exceeds maximum");
        assertTrue(ProtocolMath.validateComponentScore(score), "Fuzz risk score invalid");
        
        // Higher risk factors should generally lead to lower risk scores
        if (liquidations > 0 || leverage > 200 || volatility > 30) {
            uint256 cleanScore = ProtocolMath.calculateRiskScore(defaultMetrics);
            assertLe(score, cleanScore, "Risky metrics should not increase risk score");
        }
    }
    
    // EDGE CASE TESTS
    
    function testZeroMetrics() public {
        ProtocolMath.BehavioralMetrics memory zeroMetrics;
        
        uint256 txScore = ProtocolMath.calculateTransactionScore(zeroMetrics);
        uint256 defiScore = ProtocolMath.calculateDeFiScore(zeroMetrics);
        uint256 stakingScore = ProtocolMath.calculateStakingScore(zeroMetrics);
        uint256 riskScore = ProtocolMath.calculateRiskScore(zeroMetrics);
        uint256 historyScore = ProtocolMath.calculateHistoryScore(zeroMetrics);
        
        // All scores should be valid even with zero metrics
        assertTrue(ProtocolMath.validateComponentScore(txScore), "Zero transaction score invalid");
        assertTrue(ProtocolMath.validateComponentScore(defiScore), "Zero DeFi score invalid");
        assertTrue(ProtocolMath.validateComponentScore(stakingScore), "Zero staking score invalid");
        assertTrue(ProtocolMath.validateComponentScore(riskScore), "Zero risk score invalid");
        assertTrue(ProtocolMath.validateComponentScore(historyScore), "Zero history score invalid");
        
        emit log_named_uint("Zero Metrics TX", txScore);
        emit log_named_uint("Zero Metrics DeFi", defiScore);
        emit log_named_uint("Zero Metrics Staking", stakingScore);
        emit log_named_uint("Zero Metrics Risk", riskScore);
        emit log_named_uint("Zero Metrics History", historyScore);
    }
    
    function testMaximumMetrics() public {
        ProtocolMath.BehavioralMetrics memory maxMetrics = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 1000,
            averageTransactionValue: 1000000,
            gasEfficiencyScore: 100,
            crossChainActivityCount: 50,
            consistencyMetric: 100,
            protocolInteractionCount: 100,
            totalDeFiBalanceUSD: 10000000,
            liquidityPositionCount: 50,
            protocolDiversityScore: 100,
            totalStakedUSD: 5000000,
            stakingDurationDays: 1000,
            stakingPlatformCount: 20,
            rewardClaimFrequency: 100,
            liquidationEventCount: 0,
            leverageRatio: 100,
            portfolioVolatility: 0,
            stakingLoyaltyScore: 100,
            interactionDepthScore: 100,
            yieldFarmingActive: 1,
            accountAgeScore: 100,
            activityConsistencyScore: 100,
            engagementScore: 100
        });
        
        uint256 txScore = ProtocolMath.calculateTransactionScore(maxMetrics);
        uint256 defiScore = ProtocolMath.calculateDeFiScore(maxMetrics);
        uint256 stakingScore = ProtocolMath.calculateStakingScore(maxMetrics);
        uint256 riskScore = ProtocolMath.calculateRiskScore(maxMetrics);
        uint256 historyScore = ProtocolMath.calculateHistoryScore(maxMetrics);
        
        // All scores should still be within bounds even with maximum inputs
        assertLe(txScore, ProtocolMath.COMPONENT_MAX, "Max transaction score exceeds maximum");
        assertLe(defiScore, ProtocolMath.COMPONENT_MAX, "Max DeFi score exceeds maximum");
        assertLe(stakingScore, ProtocolMath.COMPONENT_MAX, "Max staking score exceeds maximum");
        assertLe(riskScore, ProtocolMath.COMPONENT_MAX, "Max risk score exceeds maximum");
        assertLe(historyScore, ProtocolMath.COMPONENT_MAX, "Max history score exceeds maximum");
        
        emit log_named_uint("Max Metrics TX", txScore);
        emit log_named_uint("Max Metrics DeFi", defiScore);
        emit log_named_uint("Max Metrics Staking", stakingScore);
        emit log_named_uint("Max Metrics Risk", riskScore);
        emit log_named_uint("Max Metrics History", historyScore);
    }
    
    // GOLDEN TEST VECTORS (for backend alignment)
    
    function testGoldenVectors() public {
        // Golden test case 1: Typical active user
        ProtocolMath.BehavioralMetrics memory golden1 = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 20,
            averageTransactionValue: 250,
            gasEfficiencyScore: 70,
            crossChainActivityCount: 2,
            consistencyMetric: 75,
            protocolInteractionCount: 3,
            totalDeFiBalanceUSD: 5000,
            liquidityPositionCount: 1,
            protocolDiversityScore: 40,
            totalStakedUSD: 2000,
            stakingDurationDays: 90,
            stakingPlatformCount: 1,
            rewardClaimFrequency: 4,
            liquidationEventCount: 0,
            leverageRatio: 100,
            portfolioVolatility: 30,
            stakingLoyaltyScore: 50,
            interactionDepthScore: 45,
            yieldFarmingActive: 0,
            accountAgeScore: 60,
            activityConsistencyScore: 65,
            engagementScore: 70
        });
        
        uint256 txScore1 = ProtocolMath.calculateTransactionScore(golden1);
        uint256 defiScore1 = ProtocolMath.calculateDeFiScore(golden1);
        uint256 stakingScore1 = ProtocolMath.calculateStakingScore(golden1);
        uint256 riskScore1 = ProtocolMath.calculateRiskScore(golden1);
        uint256 historyScore1 = ProtocolMath.calculateHistoryScore(golden1);
        
        // Expected ranges for this user profile
        assertGt(txScore1, 30, "Golden1 transaction score too low");
        assertLt(txScore1, 100, "Golden1 transaction score too high");
        assertGt(defiScore1, 20, "Golden1 DeFi score too low");
        assertLt(defiScore1, 80, "Golden1 DeFi score too high");
        
        emit log_named_uint("Golden1 TX", txScore1);
        emit log_named_uint("Golden1 DeFi", defiScore1);
        emit log_named_uint("Golden1 Staking", stakingScore1);
        emit log_named_uint("Golden1 Risk", riskScore1);
        emit log_named_uint("Golden1 History", historyScore1);
        
        // Store golden vectors for backend alignment
        emit log_named_uint("GOLDEN1_TX_SCORE", txScore1);
        emit log_named_uint("GOLDEN1_DEFI_SCORE", defiScore1);
        emit log_named_uint("GOLDEN1_STAKING_SCORE", stakingScore1);
        emit log_named_uint("GOLDEN1_RISK_SCORE", riskScore1);
        emit log_named_uint("GOLDEN1_HISTORY_SCORE", historyScore1);
    }
}
