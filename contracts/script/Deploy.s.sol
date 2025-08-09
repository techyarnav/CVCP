// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CreditScoreRegistry.sol";
import "../src/ProtocolMath.sol";

contract DeployScript is Script {
    
    // Deployment configuration
    struct DeployConfig {
        address initialDataProvider;
        uint256 minimumUpdateInterval;
        uint256 maxScoreHistory;
        string network;
    }
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        // Get network configuration
        DeployConfig memory config = getNetworkConfig();
        
        console.log("=== CVCP Protocol Deployment ===");
        console.log("Network:", config.network);
        console.log("Deployer:", deployer);
        console.log("Initial Data Provider:", config.initialDataProvider);
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy CreditScoreRegistry
        CreditScoreRegistry registry = new CreditScoreRegistry(config.initialDataProvider);
        
        // Configure registry parameters
        if (config.minimumUpdateInterval != 1 hours) {
            registry.updateMinimumInterval(config.minimumUpdateInterval);
        }
        
        if (config.maxScoreHistory != 100) {
            registry.updateMaxScoreHistory(config.maxScoreHistory);
        }
        
        vm.stopBroadcast();
        
        // Log deployment results - NO EMOJIS
        console.log("=== Deployment Results ===");
        console.log("CreditScoreRegistry deployed at:", address(registry));
        console.log("Minimum Update Interval:", registry.minimumUpdateInterval());
        console.log("Max Score History:", registry.maxScoreHistory());
        console.log("Data Provider Authorized:", registry.authorizedDataProviders(config.initialDataProvider));
        console.log("Owner:", registry.owner());
        
        // Verify deployment
        verifyDeployment(registry, config);
    }
    
    function getNetworkConfig() internal view returns (DeployConfig memory) {
        string memory network = vm.envOr("NETWORK", string("localhost"));
        
        if (keccak256(bytes(network)) == keccak256(bytes("scroll-sepolia"))) {
            return DeployConfig({
                initialDataProvider: vm.envAddress("DATA_PROVIDER_ADDRESS"),
                minimumUpdateInterval: 30 minutes,
                maxScoreHistory: 50,
                network: "scroll-sepolia"
            });
        } else {
            // Default localhost/testnet configuration
            return DeployConfig({
                initialDataProvider: vm.addr(vm.envUint("PRIVATE_KEY")),
                minimumUpdateInterval: 10 minutes,
                maxScoreHistory: 25,
                network: "localhost"
            });
        }
    }
    
    function verifyDeployment(CreditScoreRegistry registry, DeployConfig memory config) internal view {
        console.log("=== Deployment Verification ===");
        
        // Test ProtocolMath library
        ProtocolMath.BehavioralMetrics memory testMetrics = ProtocolMath.BehavioralMetrics({
            transactionFrequency: 10,
            averageTransactionValue: 100,
            gasEfficiencyScore: 50,
            crossChainActivityCount: 1,
            consistencyMetric: 50,
            protocolInteractionCount: 2,
            totalDeFiBalanceUSD: 1000,
            liquidityPositionCount: 1,
            protocolDiversityScore: 30,
            totalStakedUSD: 500,
            stakingDurationDays: 90,
            stakingPlatformCount: 1,
            rewardClaimFrequency: 5,
            liquidationEventCount: 0,
            leverageRatio: 100,
            portfolioVolatility: 25,
            stakingLoyaltyScore: 40,
            interactionDepthScore: 35,
            yieldFarmingActive: 0,
            accountAgeScore: 50,
            activityConsistencyScore: 45,
            engagementScore: 40
        });
        
        // Test preview functionality
        (uint256 previewScore, uint256 confidence) = registry.previewScore(testMetrics);
        
        console.log("Registry deployed successfully");
        console.log("ProtocolMath library linked");
        console.log("Preview score calculation works:", previewScore);
        console.log("Preview confidence:", confidence);
        console.log("Score in valid range:", previewScore >= ProtocolMath.MIN_SCORE && previewScore <= ProtocolMath.MAX_SCORE);
    }
}
