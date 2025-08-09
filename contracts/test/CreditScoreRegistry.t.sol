// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/CreditScoreRegistry.sol";
import "../src/ProtocolMath.sol";

contract CreditScoreRegistryTest is Test {
    CreditScoreRegistry registry;
    address owner;
    address dataProvider;
    address user;
    address unauthorized;
    
    ProtocolMath.BehavioralMetrics defaultMetrics;
    ProtocolMath.BehavioralMetrics highQualityMetrics;
    ProtocolMath.BehavioralMetrics lowQualityMetrics;
    
    event CreditScoreCalculated(
        address indexed user, 
        uint256 totalScore,
        uint256 transactionScore,
        uint256 defiScore, 
        uint256 stakingScore,
        uint256 riskScore,
        uint256 historyScore,
        uint256 confidence,
        uint256 timestamp
    );
    
    event BehavioralDataUpdated(
        address indexed user, 
        uint256 timestamp,
        uint256 dataQuality,
        address dataProvider
    );
    
    uint256 constant TEST_MINIMUM_INTERVAL = 10 minutes;

    function setUp() public {
        owner = address(this);
        dataProvider = address(0x123);
        user = address(0x456);
        unauthorized = address(0x789);
        
        // Deploy registry passing owner as initial authorized provider
        registry = new CreditScoreRegistry(owner);

        // Set minimum interval to 0 for testing
        registry.updateMinimumInterval(TEST_MINIMUM_INTERVAL);

        // Authorize additional data provider if needed
        registry.authorizeDataProvider(dataProvider);
        
        // Setup test metrics
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
            leverageRatio: 100,
            portfolioVolatility: 25,
            stakingLoyaltyScore: 65,
            interactionDepthScore: 70,
            yieldFarmingActive: 1,
            accountAgeScore: 75,
            activityConsistencyScore: 80,
            engagementScore: 85
        });
        
        highQualityMetrics = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 50,
            averageTransactionValue: 1000,
            gasEfficiencyScore: 90,
            crossChainActivityCount: 5,
            consistencyMetric: 95,
            protocolInteractionCount: 10,
            totalDeFiBalanceUSD: 50000,
            liquidityPositionCount: 5,
            protocolDiversityScore: 80,
            totalStakedUSD: 25000,
            stakingDurationDays: 365,
            stakingPlatformCount: 4,
            rewardClaimFrequency: 15,
            liquidationEventCount: 0,
            leverageRatio: 100,
            portfolioVolatility: 20,
            stakingLoyaltyScore: 85,
            interactionDepthScore: 90,
            yieldFarmingActive: 1,
            accountAgeScore: 90,
            activityConsistencyScore: 95,
            engagementScore: 95
        });
        
        lowQualityMetrics = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 1,
            averageTransactionValue: 25,
            gasEfficiencyScore: 40,
            crossChainActivityCount: 1,
            consistencyMetric: 20,
            protocolInteractionCount: 0,
            totalDeFiBalanceUSD: 0,
            liquidityPositionCount: 0,
            protocolDiversityScore: 0,
            totalStakedUSD: 0,
            stakingDurationDays: 0,
            stakingPlatformCount: 0,
            rewardClaimFrequency: 0,
            liquidationEventCount: 0,
            leverageRatio: 100,
            portfolioVolatility: 60,
            stakingLoyaltyScore: 5,
            interactionDepthScore: 10,
            yieldFarmingActive: 0,
            accountAgeScore: 15,
            activityConsistencyScore: 20,
            engagementScore: 10
        });
    }
    
    // Helper to skip the configured minimum interval
    function skipMinimumInterval() internal {
        vm.warp(block.timestamp + TEST_MINIMUM_INTERVAL + 1);
    }
    
    // AUTHORIZATION TESTS
    
    function testInitialAuthorization() public {
        assertTrue(registry.authorizedDataProviders(dataProvider), "Data provider should be authorized");
        assertTrue(registry.authorizedDataProviders(owner), "Owner should be authorized");
    }
    
    function testAuthorizeDataProvider() public {
        address newProvider = address(0xABC);
        
        // Only owner can authorize
        vm.prank(unauthorized);
        vm.expectRevert(abi.encodeWithSelector(
            Ownable.OwnableUnauthorizedAccount.selector,
            unauthorized
        ));
        registry.authorizeDataProvider(newProvider);
        
        // Owner can authorize
        registry.authorizeDataProvider(newProvider);
        assertTrue(registry.authorizedDataProviders(newProvider), "New provider should be authorized");
    }
    
    function testRevokeDataProvider() public {
        // Authorize first
        address testProvider = address(0xDEF);
        registry.authorizeDataProvider(testProvider);
        assertTrue(registry.authorizedDataProviders(testProvider), "Provider should be authorized");
        
        // Revoke authorization
        registry.revokeDataProvider(testProvider);
        assertFalse(registry.authorizedDataProviders(testProvider), "Provider should be revoked");
    }
    
    // DATA UPDATE TESTS
    
    function testUpdateBehavioralData() public {
        skipMinimumInterval();
        vm.prank(dataProvider);
        vm.expectEmit(true, false, false, false);
        emit BehavioralDataUpdated(user, block.timestamp, 100, dataProvider);
        
        registry.updateBehavioralData(user, defaultMetrics);
        
        // Verify data stored
        CreditScoreRegistry.ProcessedData memory data = registry.getBehavioralData(user);
        assertEq(data.timestamp, block.timestamp, "Timestamp should match");
        assertEq(data.dataProvider, dataProvider, "Data provider should match");
        assertGt(data.dataQualityScore, 0, "Data quality should be positive");
    }
    
    function testUpdateBehavioralDataUnauthorized() public {
        vm.prank(unauthorized);
        vm.expectRevert("Unauthorized provider");
        registry.updateBehavioralData(user, defaultMetrics);
    }
    
    function testUpdateBehavioralDataInvalidAddress() public {
        // Skip minimum interval since this is the first call
        skipMinimumInterval();
        vm.prank(dataProvider);
        vm.expectRevert("Invalid user address");
        registry.updateBehavioralData(address(0), defaultMetrics);
    }
    
    function testUpdateBehavioralDataLowQuality() public {
        // Create metrics with very low quality (all zeros)
        ProtocolMath.BehavioralMetrics memory veryLowQuality;
        
        // Skip minimum interval since this is the first call
        skipMinimumInterval();
        vm.prank(dataProvider);
        vm.expectRevert("Insufficient data quality");
        registry.updateBehavioralData(user, veryLowQuality);
    }
    
    function testUpdateIntervalEnforcement() public {
        // First update should succeed
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
        
        // Second update within interval should fail
        vm.prank(dataProvider);
        vm.expectRevert("Update too frequent");
        registry.updateBehavioralData(user, defaultMetrics);
        
        // Update after interval should succeed
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, highQualityMetrics);
    }
    
    // SCORE CALCULATION TESTS
    
    function testCalculateCreditScore() public {
        // First update behavioral data
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
        
        // Jump forward to avoid timing constraints
        skipMinimumInterval();
        
        // Calculate score
        vm.prank(dataProvider);
        vm.expectEmit(true, false, false, false);
        emit CreditScoreCalculated(user, 0, 0, 0, 0, 0, 0, 0, block.timestamp);
        
        registry.calculateCreditScore(user);
        
        // Verify score calculated
        CreditScoreRegistry.CreditScore memory score = registry.getCreditScore(user);
        assertGt(score.totalScore, ProtocolMath.MIN_SCORE - 1, "Score should be at least minimum");
        assertLe(score.totalScore, ProtocolMath.MAX_SCORE, "Score should not exceed maximum");
        assertTrue(score.isActive, "Score should be active");
        assertGt(score.confidence, 0, "Confidence should be positive");
        assertEq(score.lastUpdated, block.timestamp, "Last updated should match");
    }
    
    function testCalculateScoreWithoutData() public {
        vm.prank(dataProvider);
        vm.expectRevert("No behavioral data available");
        registry.calculateCreditScore(user);
    }
    
    function testCalculateScoreStaleData() public {
        // Add behavioral data
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
        
        // Make data stale (older than 24 hours)
        vm.warp(block.timestamp + 25 hours);
        
        vm.prank(dataProvider);
        vm.expectRevert("Data too stale");
        registry.calculateCreditScore(user);
    }
    
    function testScoreInvariantsHighQuality() public {
        // Use high quality metrics
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, highQualityMetrics);
        
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.calculateCreditScore(user);
        
        CreditScoreRegistry.CreditScore memory score = registry.getCreditScore(user);
        
        // Test protocol invariants
        assertTrue(ProtocolMath.validateFinalScore(score.totalScore), "Final score should be valid");
        assertLe(score.transactionScore, ProtocolMath.COMPONENT_MAX, "Transaction score within bounds");
        assertLe(score.defiScore, ProtocolMath.COMPONENT_MAX, "DeFi score within bounds");
        assertLe(score.stakingScore, ProtocolMath.COMPONENT_MAX, "Staking score within bounds");
        assertLe(score.riskScore, ProtocolMath.COMPONENT_MAX, "Risk score within bounds");
        assertLe(score.historyScore, ProtocolMath.COMPONENT_MAX, "History score within bounds");
        assertLe(score.confidence, 100, "Confidence within bounds");
    }
    
    function testScoreInvariantsLowQuality() public {
        // Use low quality metrics
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, lowQualityMetrics);
        
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.calculateCreditScore(user);
        
        CreditScoreRegistry.CreditScore memory score = registry.getCreditScore(user);
        
        // Even low quality should produce valid scores
        assertTrue(ProtocolMath.validateFinalScore(score.totalScore), "Final score should be valid");
        assertGe(score.totalScore, ProtocolMath.MIN_SCORE, "Score should be at least minimum");
    }
    
    // SCORE HISTORY TESTS
    
    function testScoreHistory() public {
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
        
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.calculateCreditScore(user);
        
        uint256[] memory history = registry.getScoreHistory(user);
        assertEq(history.length, 1, "History should have one entry");
        assertGt(history[0], 0, "History score should be positive");
        
        // Add another score
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, highQualityMetrics);
        
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.calculateCreditScore(user);
        
        history = registry.getScoreHistory(user);
        assertEq(history.length, 2, "History should have two entries");
        assertGt(history[1], history[0], "Second score should be higher with better metrics");
    }
    
    function testScoreHistoryLimit() public {
        // Setup user
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
        
        // Generate many scores to test history limit
        uint256 maxHistory = registry.maxScoreHistory();
        
        for (uint256 i = 0; i < maxHistory + 5; i++) {
            skipMinimumInterval();
            
            vm.prank(dataProvider);
            registry.calculateCreditScore(user);
        }
        
        uint256[] memory history = registry.getScoreHistory(user);
        assertEq(history.length, maxHistory, "History should be capped at maximum");
    }
    
    // BATCH OPERATIONS TESTS
    
    function testBatchCalculateScores() public {
        address[] memory users = new address[](3);
        users[0] = address(0x1001);
        users[1] = address(0x1002);
        users[2] = address(0x1003);
        
        // Setup behavioral data for all users
        skipMinimumInterval();
        for (uint256 i = 0; i < users.length; i++) {
            vm.prank(dataProvider);
            registry.updateBehavioralData(users[i], defaultMetrics);
        }
        
        // Batch calculate scores
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.batchCalculateScores(users);
        
        // Verify all scores calculated
        for (uint256 i = 0; i < users.length; i++) {
            CreditScoreRegistry.CreditScore memory score = registry.getCreditScore(users[i]);
            assertGt(score.totalScore, 0, "Batch score should be calculated");
            assertTrue(score.isActive, "Batch score should be active");
        }
    }
    
    function testBatchCalculateScoresTooLarge() public {
        address[] memory users = new address[](51); // Over limit of 50
        
        vm.prank(dataProvider);
        vm.expectRevert("Batch size too large");
        registry.batchCalculateScores(users);
    }
    
    // PREVIEW FUNCTIONALITY TESTS
    
    function testPreviewScore() public {
        (uint256 estimatedScore, uint256 confidence) = registry.previewScore(defaultMetrics);
        
        assertGt(estimatedScore, 0, "Preview score should be positive");
        assertGe(estimatedScore, ProtocolMath.MIN_SCORE, "Preview score should be at least minimum");
        assertLe(estimatedScore, ProtocolMath.MAX_SCORE, "Preview score should not exceed maximum");
        assertEq(confidence, 75, "Preview confidence should match expected");
        
        // Compare with actual calculation
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
        
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.calculateCreditScore(user);
        
        CreditScoreRegistry.CreditScore memory actualScore = registry.getCreditScore(user);
        
        // Preview should be close to actual (within reasonable range)
        uint256 difference = estimatedScore > actualScore.totalScore 
            ? estimatedScore - actualScore.totalScore 
            : actualScore.totalScore - estimatedScore;
        assertLt(difference, 50, "Preview should be close to actual score");
    }
    
    // ADMINISTRATIVE TESTS
    
    function testUpdateMinimumInterval() public {
        uint256 newInterval = 2 hours;
        
        registry.updateMinimumInterval(newInterval);
        assertEq(registry.minimumUpdateInterval(), newInterval, "Minimum interval should be updated");
        
        // Test bounds
        vm.expectRevert("Invalid interval");
        registry.updateMinimumInterval(5 minutes); // Too low
        
        vm.expectRevert("Invalid interval");
        registry.updateMinimumInterval(8 days); // Too high
    }
    
    function testUpdateMaxScoreHistory() public {
        uint256 newMax = 50;
        
        registry.updateMaxScoreHistory(newMax);
        assertEq(registry.maxScoreHistory(), newMax, "Max score history should be updated");
        
        // Test bounds
        vm.expectRevert("Invalid history length");
        registry.updateMaxScoreHistory(5); // Too low
        
        vm.expectRevert("Invalid history length");
        registry.updateMaxScoreHistory(2000); // Too high
    }
    
    function testPauseUnpause() public {
        // Pause contract
        registry.pause();
        
        // Operations should fail when paused
        skipMinimumInterval();
        vm.prank(dataProvider);
        vm.expectRevert(abi.encodeWithSelector(Pausable.EnforcedPause.selector));
        registry.updateBehavioralData(user, defaultMetrics);
        
        // Unpause contract
        registry.unpause();
        
        // Operations should work after unpause
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
    }
    
    // INTEGRATION TESTS
    
    function testFullWorkflow() public {
        // Step 1: Update behavioral data
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
        
        // Step 2: Calculate credit score
        vm.prank(dataProvider);
        registry.calculateCreditScore(user);
        
        // Step 3: Verify complete workflow
        CreditScoreRegistry.CreditScore memory score = registry.getCreditScore(user);
        CreditScoreRegistry.ProcessedData memory data = registry.getBehavioralData(user);
        uint256[] memory history = registry.getScoreHistory(user);
        CreditScoreRegistry.UpdateMetadata memory metadata = registry.getUpdateMetadata(user);
        
        // All data should be consistent
        assertTrue(score.isActive, "Score should be active");
        assertGt(score.totalScore, 0, "Score should be calculated");
        assertLe(data.timestamp, score.lastUpdated, "Data timestamp should be before or same as score");
        assertEq(history.length, 1, "History should have one entry");
        assertEq(history[0], score.totalScore, "History should match current score");
        assertGt(metadata.blockNumber, 0, "Metadata should be recorded");
    }
    
    // FUZZ TESTS
    
    function testFuzzScoreCalculation(uint256 txFreq, uint256 avgValue, uint256 protocolCount) public {
        // Bound inputs
        txFreq = bound(txFreq, 0, 1000);
        avgValue = bound(avgValue, 0, 100000);
        protocolCount = bound(protocolCount, 0, 50);
        
        ProtocolMath.BehavioralMetrics memory fuzzMetrics = defaultMetrics;
        fuzzMetrics.transactionFrequency = txFreq;
        fuzzMetrics.averageTransactionValue = avgValue;
        fuzzMetrics.protocolInteractionCount = protocolCount;
        
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, fuzzMetrics);
        
        skipMinimumInterval();
        
        vm.prank(dataProvider);
        registry.calculateCreditScore(user);
        
        CreditScoreRegistry.CreditScore memory score = registry.getCreditScore(user);
        
        // Score invariants must hold
        assertTrue(ProtocolMath.validateFinalScore(score.totalScore), "Fuzz score should be valid");
        assertLe(score.confidence, 100, "Fuzz confidence should be bounded");
    }
    
    // GAS OPTIMIZATION TESTS
    
    function testGasUsageScoreCalculation() public {
        skipMinimumInterval();
        vm.prank(dataProvider);
        registry.updateBehavioralData(user, defaultMetrics);
        
        skipMinimumInterval();
        uint256 gasBefore = gasleft();
        vm.prank(dataProvider);
        registry.calculateCreditScore(user);
        uint256 gasUsed = gasBefore - gasleft();
        
        // Gas usage should be reasonable (adjust based on complexity)
        assertLt(gasUsed, 500000, "Score calculation should be gas efficient");
        
        console.log("Gas used for score calculation:", gasUsed);
    }
    
    function testGasUsageBatchCalculation() public {
        address[] memory users = new address[](10);
        skipMinimumInterval();
        for (uint256 i = 0; i < users.length; i++) {
            users[i] = address(uint160(0x2000 + i));
            vm.prank(dataProvider);
            registry.updateBehavioralData(users[i], defaultMetrics);
        }
        
        skipMinimumInterval();
        uint256 gasBefore = gasleft();
        vm.prank(dataProvider);
        registry.batchCalculateScores(users);
        uint256 gasUsed = gasBefore - gasleft();
        
        console.log("Gas used for batch calculation (10 users):", gasUsed);
        console.log("Gas per user:", gasUsed / users.length);
        
        // Should be more efficient than individual calculations
        assertLt(gasUsed / users.length, 450000, "Batch should be more gas efficient");
    }
}
