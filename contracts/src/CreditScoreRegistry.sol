// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;  // Updated pragma version

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol"; 
import "@openzeppelin/contracts/utils/Pausable.sol";       
import "./ProtocolMath.sol";


/**
 * @title CreditScoreRegistry
 * @dev Complete on-chain credit score registry with advanced protocol functionality
 * Integrates with your successful DataProcessor to maintain credit scores
 */
contract CreditScoreRegistry is Ownable, ReentrancyGuard, Pausable {
    using ProtocolMath for ProtocolMath.BehavioralMetrics;
    
    // Protocol version for upgrades
    uint256 public constant PROTOCOL_VERSION = 1;
    
    /**
     * @dev Complete credit score structure
     */
    struct CreditScore {
        uint256 totalScore;          // Final score (300-850)
        uint256 transactionScore;    // Transaction component (0-200)
        uint256 defiScore;          // DeFi component (0-200)  
        uint256 stakingScore;       // Staking component (0-200)
        uint256 riskScore;          // Risk component (0-200)
        uint256 historyScore;       // History component (0-200)
        uint256 lastUpdated;        // Timestamp of last update
        uint256 confidence;         // Confidence level (0-100)
        uint256 updateCount;        // Number of updates
        bool isActive;              // Active status
    }
    
    /**
     * @dev Processed data structure for storing user metrics
     */
    struct ProcessedData {
        ProtocolMath.BehavioralMetrics metrics;
        uint256 dataQualityScore;
        uint256 timestamp;
        address dataProvider;
    }
    
    /**
     * @dev Score update metadata for ML integration
     */
    struct UpdateMetadata {
        uint256 blockNumber;
        uint256 gasUsed;
        bytes32 dataHash;
        uint256 previousScore;
    }
    
    // State mappings
    mapping(address => CreditScore) public creditScores;
    mapping(address => uint256[]) public scoreHistory;
    mapping(address => ProcessedData) public userData;
    mapping(address => UpdateMetadata) public updateMetadata;
    
    // Protocol configuration
    mapping(address => bool) public authorizedDataProviders;
    uint256 public minimumUpdateInterval = 1 hours;
    uint256 public maxScoreHistory = 100;
    
    // Events for ML model integration
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
    
    event ScoreHistoryUpdated(
        address indexed user,
        uint256 newScore,
        uint256 previousScore,
        uint256 changePercent
    );
    
    // Administrative events
    event DataProviderAuthorized(address indexed provider);
    event DataProviderRevoked(address indexed provider);
    event ProtocolParameterUpdated(string parameter, uint256 value);
    
    // Modifiers
    modifier onlyAuthorizedProvider() {
        require(authorizedDataProviders[msg.sender] || msg.sender == owner(), "Unauthorized provider");
        _;
    }
    
    modifier validUpdateInterval(address user) {
        require(
            block.timestamp >= userData[user].timestamp + minimumUpdateInterval,
            "Update too frequent"
        );
        _;
    }
    
    /**
     * @dev Initialize the registry with default authorized provider
     */
    constructor(address initialOwner) Ownable(initialOwner) {
        // Authorize the initial owner as a data provider
        authorizedDataProviders[initialOwner] = true;
        emit DataProviderAuthorized(initialOwner);
    }
    
    /**
     * @dev Update behavioral data for a user
     * Called by your DataProcessor after successful data collection
     */
    function updateBehavioralData(
        address user,
        ProtocolMath.BehavioralMetrics memory metrics
    ) 
        external 
        onlyAuthorizedProvider 
        validUpdateInterval(user)
        whenNotPaused 
    {
        require(user != address(0), "Invalid user address");
        
        // Validate metrics integrity
        require(_validateMetrics(metrics), "Invalid metrics data");
        
        // Calculate data quality
        uint256 dataQuality = _calculateDataQuality(metrics);
        require(dataQuality >= 25, "Insufficient data quality"); // Minimum 25% quality
        
        // Store processed data
        userData[user] = ProcessedData({
            metrics: metrics,
            dataQualityScore: dataQuality,
            timestamp: block.timestamp,
            dataProvider: msg.sender
        });
        
        emit BehavioralDataUpdated(user, block.timestamp, dataQuality, msg.sender);
    }
    
    /**
     * @dev Calculate comprehensive credit score for a user
     * Uses ProtocolMath library for all mathematical calculations
     */
    function calculateCreditScore(address user) 
        external 
        onlyAuthorizedProvider 
        nonReentrant 
        whenNotPaused 
    {
        ProcessedData memory data = userData[user];
        require(data.timestamp > 0, "No behavioral data available");
        require(block.timestamp <= data.timestamp + 24 hours, "Data too stale");
        
        // Execute protocol mathematical calculations
        uint256 transactionScore = ProtocolMath.calculateTransactionScore(data.metrics);
        uint256 defiScore = ProtocolMath.calculateDeFiScore(data.metrics);
        uint256 stakingScore = ProtocolMath.calculateStakingScore(data.metrics);
        uint256 riskScore = ProtocolMath.calculateRiskScore(data.metrics);
        uint256 historyScore = ProtocolMath.calculateHistoryScore(data.metrics);
        
        // Validate component scores (protocol invariant)
        require(ProtocolMath.validateComponentScore(transactionScore), "Invalid transaction score");
        require(ProtocolMath.validateComponentScore(defiScore), "Invalid DeFi score");
        require(ProtocolMath.validateComponentScore(stakingScore), "Invalid staking score");
        require(ProtocolMath.validateComponentScore(riskScore), "Invalid risk score");
        require(ProtocolMath.validateComponentScore(historyScore), "Invalid history score");
        
        // Calculate weighted total score
        uint256 totalScore = _calculateWeightedTotal(
            transactionScore,
            defiScore,
            stakingScore,
            riskScore,
            historyScore
        );
        
        // Normalize to valid range (300-850)
        totalScore = _normalizeToRange(totalScore);
        
        // Validate final score (protocol invariant)
        require(ProtocolMath.validateFinalScore(totalScore), "Invalid final score");
        
        // Calculate confidence based on data quality
        uint256 confidence = _calculateConfidence(data.dataQualityScore, data.metrics);
        
        // Store previous score for change tracking
        uint256 previousScore = creditScores[user].totalScore;
        
        // Update credit score record
        _updateCreditScore(
            user,
            totalScore,
            transactionScore,
            defiScore,
            stakingScore,
            riskScore,
            historyScore,
            confidence
        );
        
        // Track score changes for ML models
        if (previousScore > 0) {
            uint256 changePercent = _calculateChangePercent(previousScore, totalScore);
            emit ScoreHistoryUpdated(user, totalScore, previousScore, changePercent);
        }
        
        // Emit comprehensive event for ML model consumption
        emit CreditScoreCalculated(
            user,
            totalScore,
            transactionScore,
            defiScore,
            stakingScore,
            riskScore,
            historyScore,
            confidence,
            block.timestamp
        );
    }
    
    /**
     * @dev Calculate weighted total score using protocol weights
     */
    function _calculateWeightedTotal(
        uint256 transactionScore,
        uint256 defiScore,
        uint256 stakingScore,
        uint256 riskScore,
        uint256 historyScore
    ) internal pure returns (uint256) {
        return (
            transactionScore * ProtocolMath.TRANSACTION_WEIGHT +
            defiScore * ProtocolMath.DEFI_WEIGHT +
            stakingScore * ProtocolMath.STAKING_WEIGHT +
            riskScore * ProtocolMath.RISK_WEIGHT +
            historyScore * ProtocolMath.HISTORY_WEIGHT
        ) / 100;
    }
    
    /**
     * @dev Normalize total score to valid credit score range
     */
    function _normalizeToRange(uint256 totalScore) internal pure returns (uint256) {
        // Map from 0-1000 component range to 300-850 credit score range
        uint256 normalizedScore = (totalScore * 550) / 1000 + 300;
        
        if (normalizedScore < ProtocolMath.MIN_SCORE) return ProtocolMath.MIN_SCORE;
        if (normalizedScore > ProtocolMath.MAX_SCORE) return ProtocolMath.MAX_SCORE;
        
        return normalizedScore;
    }
    
    /**
     * @dev Calculate data quality score based on available metrics
     */
    function _calculateDataQuality(ProtocolMath.BehavioralMetrics memory metrics) 
        internal pure returns (uint256) {
        
        uint256 qualityScore = 0;
        
        // Transaction data quality (45 points max)
        if (metrics.transactionFrequency > 0) qualityScore += 20;
        if (metrics.averageTransactionValue > 0) qualityScore += 15;
        if (metrics.crossChainActivityCount > 1) qualityScore += 10;
        
        // DeFi data quality (35 points max)
        if (metrics.protocolInteractionCount > 0) qualityScore += 20;
        if (metrics.totalDeFiBalanceUSD > 0) qualityScore += 15;
        
        // Staking data quality (20 points max)
        if (metrics.totalStakedUSD > 0) qualityScore += 20;
        
        return qualityScore;
    }
    
    /**
     * @dev Calculate confidence score based on data quality and metrics
     */
    function _calculateConfidence(uint256 dataQuality, ProtocolMath.BehavioralMetrics memory metrics) 
        internal pure returns (uint256) {
        
        uint256 baseConfidence = dataQuality;
        
        // Bonus confidence for comprehensive activity
        if (metrics.transactionFrequency > 10) baseConfidence += 5;
        if (metrics.protocolInteractionCount > 3) baseConfidence += 5;
        if (metrics.stakingDurationDays > 30) baseConfidence += 10;
        if (metrics.crossChainActivityCount > 2) baseConfidence += 5;
        
        // Advanced activity bonuses
        if (metrics.interactionDepthScore > 50) baseConfidence += 5;
        if (metrics.yieldFarmingActive > 0) baseConfidence += 3;
        if (metrics.stakingLoyaltyScore > 70) baseConfidence += 7;
        
        return baseConfidence > 100 ? 100 : baseConfidence;
    }
    
    /**
     * @dev Validate metrics data integrity
     */
    function _validateMetrics(ProtocolMath.BehavioralMetrics memory metrics) 
        internal pure returns (bool) {
        
        // Check for reasonable bounds
        if (metrics.gasEfficiencyScore > 100) return false;
        if (metrics.consistencyMetric > 100) return false;
        if (metrics.protocolDiversityScore > 100) return false;
        if (metrics.portfolioVolatility > 100) return false;
        if (metrics.leverageRatio > 10000) return false; // Max 100x leverage
        
        return true;
    }
    
    /**
     * @dev Update credit score record with comprehensive tracking
     */
    function _updateCreditScore(
        address user,
        uint256 totalScore,
        uint256 transactionScore,
        uint256 defiScore,
        uint256 stakingScore,
        uint256 riskScore,
        uint256 historyScore,
        uint256 confidence
    ) internal {
        CreditScore storage score = creditScores[user];
        
        score.totalScore = totalScore;
        score.transactionScore = transactionScore;
        score.defiScore = defiScore;
        score.stakingScore = stakingScore;
        score.riskScore = riskScore;
        score.historyScore = historyScore;
        score.lastUpdated = block.timestamp;
        score.confidence = confidence;
        score.updateCount++;
        score.isActive = true;
        
        // Manage score history (limit to maxScoreHistory)
        scoreHistory[user].push(totalScore);
        if (scoreHistory[user].length > maxScoreHistory) {
            // Remove oldest score to maintain limit
            for (uint i = 0; i < scoreHistory[user].length - 1; i++) {
                scoreHistory[user][i] = scoreHistory[user][i + 1];
            }
            scoreHistory[user].pop();
        }
        
        // Store update metadata for ML models
        updateMetadata[user] = UpdateMetadata({
            blockNumber: block.number,
            gasUsed: gasleft(),
            dataHash: keccak256(abi.encode(userData[user].metrics)),
            previousScore: scoreHistory[user].length > 1 ? scoreHistory[user][scoreHistory[user].length - 2] : 0
        });
    }
    
    /**
     * @dev Calculate percentage change between scores
     */
    function _calculateChangePercent(uint256 oldScore, uint256 newScore) 
        internal pure returns (uint256) {
        
        if (oldScore == 0) return 0;
        
        uint256 change = newScore > oldScore ? newScore - oldScore : oldScore - newScore;
        return (change * 100) / oldScore;
    }
    
    // PUBLIC VIEW FUNCTIONS
    
    /**
     * @dev Get complete credit score for a user
     */
    function getCreditScore(address user) external view returns (CreditScore memory) {
        return creditScores[user];
    }
    
    /**
     * @dev Get score history for a user
     */
    function getScoreHistory(address user) external view returns (uint256[] memory) {
        return scoreHistory[user];
    }
    
    /**
     * @dev Get behavioral data for a user
     */
    function getBehavioralData(address user) external view returns (ProcessedData memory) {
        return userData[user];
    }
    
    /**
     * @dev Preview score calculation without executing
     * Useful for ML model training and user preview
     */
    function previewScore(ProtocolMath.BehavioralMetrics memory metrics) 
        external pure returns (uint256 estimatedScore, uint256 confidence) {
        
        uint256 transactionScore = ProtocolMath.calculateTransactionScore(metrics);
        uint256 defiScore = ProtocolMath.calculateDeFiScore(metrics);
        uint256 stakingScore = ProtocolMath.calculateStakingScore(metrics);
        uint256 riskScore = ProtocolMath.calculateRiskScore(metrics);
        uint256 historyScore = ProtocolMath.calculateHistoryScore(metrics);
        
        uint256 totalScore = (
            transactionScore * ProtocolMath.TRANSACTION_WEIGHT +
            defiScore * ProtocolMath.DEFI_WEIGHT +
            stakingScore * ProtocolMath.STAKING_WEIGHT +
            riskScore * ProtocolMath.RISK_WEIGHT +
            historyScore * ProtocolMath.HISTORY_WEIGHT
        ) / 100;
        
        estimatedScore = (totalScore * 550) / 1000 + 300;
        if (estimatedScore < ProtocolMath.MIN_SCORE) estimatedScore = ProtocolMath.MIN_SCORE;
        if (estimatedScore > ProtocolMath.MAX_SCORE) estimatedScore = ProtocolMath.MAX_SCORE;
        
        // Simplified confidence for preview
        confidence = 75; // Base confidence for preview
    }
    
    /**
     * @dev Get update metadata for ML analysis
     */
    function getUpdateMetadata(address user) external view returns (UpdateMetadata memory) {
        return updateMetadata[user];
    }
    
    // ADMINISTRATIVE FUNCTIONS
    
    /**
     * @dev Authorize a new data provider
     */
    function authorizeDataProvider(address provider) external onlyOwner {
        require(provider != address(0), "Invalid provider address");
        authorizedDataProviders[provider] = true;
        emit DataProviderAuthorized(provider);
    }
    
    /**
     * @dev Revoke data provider authorization
     */
    function revokeDataProvider(address provider) external onlyOwner {
        authorizedDataProviders[provider] = false;
        emit DataProviderRevoked(provider);
    }
    
    /**
     * @dev Update protocol parameters
     */
    function updateMinimumInterval(uint256 newInterval) external onlyOwner {
        require(newInterval >= 10 minutes && newInterval <= 7 days, "Invalid interval");
        minimumUpdateInterval = newInterval;
        emit ProtocolParameterUpdated("minimumUpdateInterval", newInterval);
    }
    
    /**
     * @dev Update maximum score history length
     */
    function updateMaxScoreHistory(uint256 newMax) external onlyOwner {
        require(newMax >= 10 && newMax <= 1000, "Invalid history length");
        maxScoreHistory = newMax;
        emit ProtocolParameterUpdated("maxScoreHistory", newMax);
    }
    
    /**
     * @dev Emergency pause function
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause function
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Batch score calculation for multiple users
     * Optimized for gas efficiency
     */
    function batchCalculateScores(address[] calldata users) 
        external 
        onlyAuthorizedProvider 
        whenNotPaused 
    {
        require(users.length <= 50, "Batch size too large"); // Gas limit protection
        
        for (uint256 i = 0; i < users.length; i++) {
            if (userData[users[i]].timestamp > 0 && 
                block.timestamp >= userData[users[i]].timestamp + minimumUpdateInterval) {
                
                // Inline score calculation for gas efficiency
                ProcessedData memory data = userData[users[i]];
                
                uint256 totalScore = (
                    ProtocolMath.calculateTransactionScore(data.metrics) * ProtocolMath.TRANSACTION_WEIGHT +
                    ProtocolMath.calculateDeFiScore(data.metrics) * ProtocolMath.DEFI_WEIGHT +
                    ProtocolMath.calculateStakingScore(data.metrics) * ProtocolMath.STAKING_WEIGHT +
                    ProtocolMath.calculateRiskScore(data.metrics) * ProtocolMath.RISK_WEIGHT +
                    ProtocolMath.calculateHistoryScore(data.metrics) * ProtocolMath.HISTORY_WEIGHT
                ) / 100;
                
                totalScore = _normalizeToRange(totalScore);
                uint256 confidence = _calculateConfidence(data.dataQualityScore, data.metrics);
                
                creditScores[users[i]].totalScore = totalScore;
                creditScores[users[i]].confidence = confidence;
                creditScores[users[i]].lastUpdated = block.timestamp;
                creditScores[users[i]].isActive = true;
                
                scoreHistory[users[i]].push(totalScore);
            }
        }
    }
}
