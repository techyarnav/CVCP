// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title DataValidator
 * @dev Validation utilities for behavioral metrics
 */
library DataValidator {
    
    struct ValidationResult {
        bool isValid;
        string errorMessage;
        uint256 confidence;
    }
    
    /**
     * @dev Validate behavioral metrics completeness and integrity
     */
    function validateBehavioralMetrics(
        uint256 transactionFreq,
        uint256 avgValue,
        uint256 protocolCount,
        uint256 stakedAmount
    ) external pure returns (ValidationResult memory) {
        
        if (transactionFreq == 0 && avgValue == 0 && protocolCount == 0 && stakedAmount == 0) {
            return ValidationResult(false, "No activity data", 0);
        }
        
        if (avgValue > 10000000) { // $10M cap
            return ValidationResult(false, "Transaction value too high", 0);
        }
        
        if (protocolCount > 100) {
            return ValidationResult(false, "Protocol count unrealistic", 0);
        }
        
        uint256 confidence = 100;
        if (transactionFreq == 0) confidence -= 20;
        if (protocolCount == 0) confidence -= 15;
        if (stakedAmount == 0) confidence -= 10;
        
        return ValidationResult(true, "", confidence);
    }
}
