# backend/services/data_processor.py

import asyncio
import sys
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
from loguru import logger

# Fix the import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import asyncio
import sys
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
from loguru import logger

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from clients.multi_chain_aggregator import MultiChainDataAggregator

class DataProcessor:
    """
    Processes raw API data into structured format for smart contracts
    Transforms comprehensive data into exact integer format required by protocol
    """
    
    def __init__(self):
        self.aggregator = MultiChainDataAggregator()
        
        # Data quality thresholds
        self.quality_thresholds = {
            'min_transactions': 5,
            'min_chains': 1,
            'min_data_points': 3,
            'staleness_hours': 24
        }
        
        # Processing configuration
        self.processing_config = {
            'max_usd_value_cap': 10_000_000,  # Cap extreme values
            'min_percentage_threshold': 1,    # Minimum percentage for calculations
            'default_gas_efficiency': 50,     # Default gas efficiency score
            'consistency_weight': 0.6,        # Weight for consistency calculations
            'volatility_smoothing': 0.8       # Smoothing factor for volatility
        }
    
    async def process_user_behavioral_data(self, address: str) -> Tuple[Dict[str, int], Dict[str, Any]]:
        """
        Main processing function - converts raw API data to contract-ready format
        
        Returns:
            Tuple[Dict[str, int], Dict[str, Any]]: (contract_metrics, processing_metadata)
        """
        
        logger.info(f"Starting behavioral data processing for address: {address}")
        
        try:
            # Step 1: Collect comprehensive raw data
            raw_data = await self.aggregator.fetch_user_comprehensive_data(address)
            
            # Step 2: Validate data quality
            data_quality = self._validate_data_quality(raw_data)
            
            if not data_quality['is_valid']:
                logger.warning(f"Data quality issues for {address}: {data_quality['issues']}")
            
            # Step 3: Extract and process behavioral metrics
            behavioral_metrics = self._extract_behavioral_metrics(raw_data)
            
            # Step 4: Apply smart contract formatting
            contract_metrics = self._format_for_smart_contract(behavioral_metrics)
            
            # Step 5: Generate processing metadata
            processing_metadata = self._generate_processing_metadata(
                raw_data, behavioral_metrics, contract_metrics, data_quality
            )
            
            logger.info(f"Successfully processed behavioral data for {address}")
            logger.info(f"Contract metrics preview: Total Score Components = {sum(contract_metrics.values())}")
            
            return contract_metrics, processing_metadata
            
        except Exception as e:
            logger.error(f"Error processing behavioral data for {address}: {str(e)}")
            
            # Return fallback metrics with error information
            fallback_metrics = self._get_fallback_metrics()
            error_metadata = {
                'processing_status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'fallback_used': True
            }
            
            return fallback_metrics, error_metadata
    
    def _validate_data_quality(self, raw_data: Dict) -> Dict[str, Any]:
        """Validate the quality of collected data"""
        
        issues = []
        quality_score = 0
        
        # Check collection status
        collection_status = raw_data.get('collection_status', {})
        successful_sources = sum(1 for status in collection_status.values() 
                               if status.get('success', False))
        
        if successful_sources == 0:
            issues.append("No successful data sources")
        else:
            quality_score += successful_sources * 25  # 25 points per successful source
        
        # Check data freshness
        collection_time = raw_data.get('collection_timestamp')
        if collection_time:
            try:
                collection_dt = datetime.fromisoformat(collection_time)
                age_hours = (datetime.now() - collection_dt).total_seconds() / 3600
                
                if age_hours > self.quality_thresholds['staleness_hours']:
                    issues.append(f"Data is {age_hours:.1f} hours old")
                else:
                    quality_score += 25  # Freshness bonus
            except Exception:
                issues.append("Invalid collection timestamp")
        
        # Check data completeness
        structured_metrics = raw_data.get('structured_metrics', {})
        if structured_metrics:
            quality_score += 25  # Structured data bonus
        
        # Check user analytics
        user_analytics = raw_data.get('user_analytics', {})
        if user_analytics.get('user_category') != 'newcomer':
            quality_score += 25  # Activity bonus
        
        return {
            'is_valid': len(issues) == 0 or quality_score >= 50,
            'quality_score': min(100, quality_score),
            'issues': issues,
            'successful_sources': successful_sources,
            'recommendation': 'proceed' if quality_score >= 50 else 'retry_collection'
        }
    
    def _extract_behavioral_metrics(self, raw_data: Dict) -> Dict[str, Any]:
        """Extract and compute behavioral metrics from raw data"""
        
        # Extract data sections safely
        structured_metrics = raw_data.get('structured_metrics', {})
        user_analytics = raw_data.get('user_analytics', {})
        collection_status = raw_data.get('collection_status', {})
        
        # Process transaction data
        transaction_data = self._process_transaction_data(
            structured_metrics.get('transaction_metrics', {}),
            collection_status.get('alchemy', {})
        )
        
        # Process DeFi data
        defi_data = self._process_defi_data(
            structured_metrics.get('defi_metrics', {}),
            collection_status.get('zapper', {})
        )
        
        # Process staking data
        staking_data = self._process_staking_data(
            structured_metrics.get('staking_metrics', {}),
            collection_status.get('moralis', {})
        )
        
        # Process risk metrics
        risk_data = self._process_risk_data(raw_data, user_analytics)
        
        # Process historical patterns
        history_data = self._process_history_data(raw_data, user_analytics)
        
        return {
            'transaction_metrics': transaction_data,
            'defi_metrics': defi_data,
            'staking_metrics': staking_data,
            'risk_metrics': risk_data,
            'history_metrics': history_data,
            'meta_metrics': self._calculate_meta_metrics(raw_data)
        }
    
    def _process_transaction_data(self, tx_data: Dict, status_data: Dict) -> Dict[str, Any]:
        """Process transaction-related metrics"""
        
        # Safe extraction with defaults
        monthly_txns = tx_data.get('monthly_txn_count', 0)
        avg_value = float(tx_data.get('avg_value_usd', 0) or 0)
        gas_efficiency = tx_data.get('gas_efficiency', self.processing_config['default_gas_efficiency'])
        active_chains = tx_data.get('active_chains', 0)
        consistency = tx_data.get('consistency_score', 0)
        total_transactions = tx_data.get('total_transactions', 0)
        
        # Apply processing logic
        processed_avg_value = min(avg_value, self.processing_config['max_usd_value_cap'])
        
        # Calculate frequency score (0-100 scale)
        frequency_score = min(100, monthly_txns * 2)  # 2 points per monthly transaction
        
        # Normalize consistency (0-100 scale)
        consistency_normalized = max(0, min(100, consistency))
        
        # Cross-chain activity score
        cross_chain_score = min(100, active_chains * 25)  # 25 points per chain
        
        return {
            'transactionFrequency': frequency_score,
            'averageTransactionValue': int(processed_avg_value),
            'gasEfficiencyScore': int(gas_efficiency),
            'crossChainActivityCount': active_chains,
            'consistencyMetric': int(consistency_normalized),
            'totalTransactionCount': total_transactions,
            'rawMonthlyCount': monthly_txns,
            'dataSource': 'alchemy',
            'dataQuality': 100 if status_data.get('success') else 25
        }
    
    def _process_defi_data(self, defi_data: Dict, status_data: Dict) -> Dict[str, Any]:
        """Process DeFi-related metrics"""
        
        # Safe extraction
        unique_protocols = defi_data.get('unique_protocols', 0)
        total_balance = float(defi_data.get('total_balance_usd', 0) or 0)
        lp_positions = defi_data.get('lp_positions', 0)
        diversity_score = defi_data.get('diversity_score', 0)
        interaction_depth = defi_data.get('interaction_depth_score', 0)
        yield_farming = defi_data.get('yield_farming_active', 0)
        
        # Process values
        capped_balance = min(total_balance, self.processing_config['max_usd_value_cap'])
        
        # Calculate derived metrics
        protocol_interaction_score = min(100, unique_protocols * 10)  # 10 points per protocol
        liquidity_score = min(100, lp_positions * 20)  # 20 points per LP position
        diversity_normalized = max(0, min(100, diversity_score))
        interaction_depth_normalized = max(0, min(100, interaction_depth))
        
        return {
            'protocolInteractionCount': unique_protocols,
            'totalDeFiBalanceUSD': int(capped_balance),
            'liquidityPositionCount': lp_positions,
            'protocolDiversityScore': int(diversity_normalized),
            'interactionDepthScore': int(interaction_depth_normalized),
            'yieldFarmingActive': int(bool(yield_farming)),
            'protocolInteractionScore': protocol_interaction_score,
            'dataSource': 'zapper',
            'dataQuality': 100 if status_data.get('success') else 25
        }
    
    def _process_staking_data(self, staking_data: Dict, status_data: Dict) -> Dict[str, Any]:
        """Process staking-related metrics"""
        
        # Safe extraction
        total_staked = float(staking_data.get('total_staked_usd', 0) or 0)
        duration_days = staking_data.get('avg_duration_days', 0)
        platform_count = staking_data.get('platform_count', 0)
        claim_frequency = staking_data.get('claim_frequency', 0)
        loyalty_score = staking_data.get('staking_loyalty_score', 0)
        sophistication = staking_data.get('sophistication_score', 0)
        
        # Process values
        capped_staked = min(total_staked, self.processing_config['max_usd_value_cap'])
        
        # Calculate derived metrics
        duration_score = min(100, duration_days / 3.65)  # Normalize to 100 (365 days = 100)
        platform_diversity = min(100, platform_count * 20)  # 20 points per platform
        reward_claim_score = min(100, claim_frequency * 5)  # 5 points per claim
        
        return {
            'totalStakedUSD': int(capped_staked),
            'stakingDurationDays': int(duration_days),
            'stakingPlatformCount': platform_count,
            'rewardClaimFrequency': claim_frequency,
            'stakingLoyaltyScore': int(loyalty_score),
            'platformDiversityScore': platform_diversity,
            'stakingSophisticationScore': int(sophistication),
            'dataSource': 'moralis',
            'dataQuality': 100 if status_data.get('success') else 25
        }
    
    def _process_risk_data(self, raw_data: Dict, user_analytics: Dict) -> Dict[str, Any]:
        """Process risk-related metrics"""
        
        # Extract risk indicators
        portfolio_value = user_analytics.get('total_portfolio_value_usd', 0)
        user_category = user_analytics.get('user_category', 'newcomer')
        
        # Calculate risk metrics (placeholder implementation)
        liquidation_events = 0  # Would be calculated from transaction history
        leverage_ratio = 100    # Default 1x leverage (100 = 1.0x)
        portfolio_volatility = self._calculate_portfolio_volatility(raw_data)
        
        # Risk scoring
        risk_category_score = self._get_risk_category_score(user_category)
        volatility_score = max(0, 100 - portfolio_volatility * 2)  # Lower volatility = higher score
        
        return {
            'liquidationEventCount': liquidation_events,
            'leverageRatio': leverage_ratio,
            'portfolioVolatility': int(portfolio_volatility),
            'riskCategoryScore': risk_category_score,
            'volatilityScore': int(volatility_score),
            'portfolioValueUSD': int(min(portfolio_value, self.processing_config['max_usd_value_cap'])),
            'userCategory': user_category
        }
    
    def _process_history_data(self, raw_data: Dict, user_analytics: Dict) -> Dict[str, Any]:
        """Process historical behavior patterns"""
        
        # Extract historical data
        data_quality = raw_data.get('data_quality_analysis', {})
        overall_quality = data_quality.get('overall_quality_score', 0)
        activity_score = user_analytics.get('overall_activity_score', 0)
        
        # Calculate history metrics
        account_age_score = 50  # Placeholder - would calculate from first transaction
        activity_consistency = overall_quality  # Use data quality as proxy for consistency
        engagement_score = min(100, activity_score)
        
        return {
            'accountAgeScore': account_age_score,
            'activityConsistencyScore': int(activity_consistency),
            'engagementScore': int(engagement_score),
            'overallQualityScore': int(overall_quality),
            'dataCompletenessScore': data_quality.get('completeness_percentage', 0)
        }
    
    def _calculate_portfolio_volatility(self, raw_data: Dict) -> float:
        """Calculate portfolio volatility estimate"""
        
        # Simple volatility calculation based on available data
        user_analytics = raw_data.get('user_analytics', {})
        user_category = user_analytics.get('user_category', 'newcomer')
        
        # Map user categories to volatility estimates
        volatility_map = {
            'whale_power_user': 15,
            'advanced_defi_user': 25,
            'active_defi_user': 30,
            'staking_focused_user': 20,
            'active_crypto_user': 35,
            'casual_user': 40,
            'newcomer': 50
        }
        
        return volatility_map.get(user_category, 40)
    
    def _get_risk_category_score(self, user_category: str) -> int:
        """Get risk score based on user category"""
        
        risk_scores = {
            'whale_power_user': 90,
            'advanced_defi_user': 75,
            'active_defi_user': 65,
            'staking_focused_user': 80,
            'active_crypto_user': 60,
            'casual_user': 50,
            'newcomer': 40
        }
        
        return risk_scores.get(user_category, 40)
    
    def _calculate_meta_metrics(self, raw_data: Dict) -> Dict[str, Any]:
        """Calculate meta-metrics about the data collection process"""
        
        collection_status = raw_data.get('collection_status', {})
        
        successful_sources = sum(1 for status in collection_status.values() 
                               if status.get('success', False))
        
        total_collection_time = sum(status.get('collection_time', 0) 
                                  for status in collection_status.values())
        
        return {
            'successfulSources': successful_sources,
            'totalSources': len(collection_status),
            'successRate': int((successful_sources / max(1, len(collection_status))) * 100),
            'totalCollectionTime': int(total_collection_time),
            'averageCollectionTime': int(total_collection_time / max(1, len(collection_status)))
        }
    
    def _format_for_smart_contract(self, behavioral_metrics: Dict) -> Dict[str, int]:
        """Format behavioral metrics for smart contract consumption"""
        
        tx_metrics = behavioral_metrics['transaction_metrics']
        defi_metrics = behavioral_metrics['defi_metrics']
        staking_metrics = behavioral_metrics['staking_metrics']
        risk_metrics = behavioral_metrics['risk_metrics']
        history_metrics = behavioral_metrics['history_metrics']
        
        # Ensure all values are integers for Solidity compatibility
        contract_metrics = {
            # Transaction metrics (uint256)
            'transactionFrequency': int(tx_metrics['transactionFrequency']),
            'averageTransactionValue': int(tx_metrics['averageTransactionValue']),
            'gasEfficiencyScore': int(tx_metrics['gasEfficiencyScore']),
            'crossChainActivityCount': int(tx_metrics['crossChainActivityCount']),
            'consistencyMetric': int(tx_metrics['consistencyMetric']),
            
            # DeFi metrics (uint256)
            'protocolInteractionCount': int(defi_metrics['protocolInteractionCount']),
            'totalDeFiBalanceUSD': int(defi_metrics['totalDeFiBalanceUSD']),
            'liquidityPositionCount': int(defi_metrics['liquidityPositionCount']),
            'protocolDiversityScore': int(defi_metrics['protocolDiversityScore']),
            'interactionDepthScore': int(defi_metrics['interactionDepthScore']),
            'yieldFarmingActive': int(defi_metrics['yieldFarmingActive']),
            
            # Staking metrics (uint256)
            'totalStakedUSD': int(staking_metrics['totalStakedUSD']),
            'stakingDurationDays': int(staking_metrics['stakingDurationDays']),
            'stakingPlatformCount': int(staking_metrics['stakingPlatformCount']),
            'rewardClaimFrequency': int(staking_metrics['rewardClaimFrequency']),
            'stakingLoyaltyScore': int(staking_metrics['stakingLoyaltyScore']),
            'platformDiversityScore': int(staking_metrics['platformDiversityScore']),
            
            # Risk metrics (uint256)
            'liquidationEventCount': int(risk_metrics['liquidationEventCount']),
            'leverageRatio': int(risk_metrics['leverageRatio']),
            'portfolioVolatility': int(risk_metrics['portfolioVolatility']),
            
            # History metrics (uint256)
            'accountAgeScore': int(history_metrics['accountAgeScore']),
            'activityConsistencyScore': int(history_metrics['activityConsistencyScore']),
            'engagementScore': int(history_metrics['engagementScore'])
        }
        
        # Validate all values are within acceptable ranges
        for key, value in contract_metrics.items():
            if not isinstance(value, int):
                logger.warning(f"Non-integer value found for {key}: {value}")
                contract_metrics[key] = int(value)
            
            # Ensure non-negative values
            if value < 0:
                logger.warning(f"Negative value found for {key}: {value}")
                contract_metrics[key] = 0
            
            # Cap extremely large values
            if value > 1_000_000_000:  # 1 billion cap
                logger.warning(f"Extremely large value capped for {key}: {value}")
                contract_metrics[key] = 1_000_000_000
        
        return contract_metrics
    
    def _generate_processing_metadata(self, raw_data: Dict, behavioral_metrics: Dict, 
                                    contract_metrics: Dict, data_quality: Dict) -> Dict[str, Any]:
        """Generate comprehensive processing metadata"""
        
        return {
            'processing_status': 'success',
            'processing_timestamp': datetime.now().isoformat(),
            'data_quality': data_quality,
            'input_data_summary': {
                'collection_status': raw_data.get('collection_status', {}),
                'user_category': raw_data.get('user_analytics', {}).get('user_category', 'unknown'),
                'data_grade': raw_data.get('data_quality_analysis', {}).get('quality_grade', 'F')
            },
            'processing_summary': {
                'metrics_extracted': len(behavioral_metrics),
                'contract_metrics_count': len(contract_metrics),
                'total_score_preview': sum(contract_metrics.values()),
                'processing_version': '1.0.0'
            },
            'validation_results': {
                'all_integers': all(isinstance(v, int) for v in contract_metrics.values()),
                'no_negative_values': all(v >= 0 for v in contract_metrics.values()),
                'within_bounds': all(v <= 1_000_000_000 for v in contract_metrics.values())
            },
            'recommendations': self._generate_recommendations(behavioral_metrics, data_quality),
            'fallback_used': False
        }
    
    def _generate_recommendations(self, behavioral_metrics: Dict, data_quality: Dict) -> List[str]:
        """Generate recommendations based on processed data"""
        
        recommendations = []
        
        # Data quality recommendations
        if data_quality['quality_score'] < 70:
            recommendations.append("Consider improving data collection completeness")
        
        if data_quality['successful_sources'] < 2:
            recommendations.append("Multiple data sources recommended for better accuracy")
        
        # Behavioral recommendations
        tx_metrics = behavioral_metrics['transaction_metrics']
        if tx_metrics['transactionFrequency'] < 10:
            recommendations.append("Low transaction activity may affect score accuracy")
        
        defi_metrics = behavioral_metrics['defi_metrics']
        if defi_metrics['protocolInteractionCount'] == 0:
            recommendations.append("DeFi interaction data missing - consider protocol engagement")
        
        staking_metrics = behavioral_metrics['staking_metrics']
        if staking_metrics['totalStakedUSD'] == 0:
            recommendations.append("No staking activity detected - consider staking for credit building")
        
        return recommendations
    
    def _get_fallback_metrics(self) -> Dict[str, int]:
        """Return safe fallback metrics for error cases"""
        
        return {
            # Transaction metrics
            'transactionFrequency': 0,
            'averageTransactionValue': 0,
            'gasEfficiencyScore': 50,
            'crossChainActivityCount': 0,
            'consistencyMetric': 0,
            
            # DeFi metrics
            'protocolInteractionCount': 0,
            'totalDeFiBalanceUSD': 0,
            'liquidityPositionCount': 0,
            'protocolDiversityScore': 0,
            'interactionDepthScore': 0,
            'yieldFarmingActive': 0,
            
            # Staking metrics
            'totalStakedUSD': 0,
            'stakingDurationDays': 0,
            'stakingPlatformCount': 0,
            'rewardClaimFrequency': 0,
            'stakingLoyaltyScore': 0,
            'platformDiversityScore': 0,
            
            # Risk metrics
            'liquidationEventCount': 0,
            'leverageRatio': 100,
            'portfolioVolatility': 50,
            
            # History metrics
            'accountAgeScore': 0,
            'activityConsistencyScore': 0,
            'engagementScore': 0
        }
    
    # Additional utility methods
    
    async def preview_contract_data(self, address: str) -> Dict[str, Any]:
        """Preview what would be sent to smart contract without processing"""
        
        try:
            contract_metrics, metadata = await self.process_user_behavioral_data(address)
            
            return {
                'address': address,
                'contract_ready_data': contract_metrics,
                'processing_metadata': metadata,
                'estimated_total_score': sum(contract_metrics.values()),
                'data_quality_grade': metadata.get('input_data_summary', {}).get('data_grade', 'F'),
                'recommendations': metadata.get('recommendations', [])
            }
            
        except Exception as e:
            logger.error(f"Error in preview for {address}: {str(e)}")
            return {
                'error': str(e),
                'fallback_data': self._get_fallback_metrics()
            }
    
    def validate_contract_format(self, contract_metrics: Dict[str, int]) -> Dict[str, Any]:
        """Validate that contract metrics are properly formatted"""
        
        validation_results = {
            'is_valid': True,
            'issues': [],
            'metrics_count': len(contract_metrics),
            'total_value': 0  # Will calculate after validation
        }
        
        # Check data types
        for key, value in contract_metrics.items():
            if not isinstance(value, int):
                validation_results['is_valid'] = False
                validation_results['issues'].append(f"{key} is not an integer: {type(value)}")
            elif value < 0:  # Only check negative for integers
                validation_results['is_valid'] = False
                validation_results['issues'].append(f"{key} has negative value: {value}")
        
        # Check required fields
        required_fields = [
            'transactionFrequency', 'averageTransactionValue', 'gasEfficiencyScore',
            'protocolInteractionCount', 'totalDeFiBalanceUSD', 'totalStakedUSD',
            'liquidationEventCount', 'leverageRatio', 'portfolioVolatility'
        ]
        
        for field in required_fields:
            if field not in contract_metrics:
                validation_results['is_valid'] = False
                validation_results['issues'].append(f"Missing required field: {field}")
        
        # Calculate total value safely (only for integer values)
        try:
            validation_results['total_value'] = sum(v for v in contract_metrics.values() if isinstance(v, int))
        except Exception:
            validation_results['total_value'] = 0
        
        return validation_results
    
    def _convert_to_behavioral_metrics_format(self, contract_metrics: Dict[str, int], processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert contract metrics back to BehavioralMetrics format for contract bridge"""
        
        return {
            'transactionFrequency': contract_metrics.get('transactionFrequency', 0),
            'averageTransactionValue': contract_metrics.get('averageTransactionValue', 0),
            'gasEfficiencyScore': contract_metrics.get('gasEfficiencyScore', 50),
            'crossChainActivityCount': contract_metrics.get('crossChainActivityCount', 0),
            'consistencyMetric': contract_metrics.get('consistencyMetric', 0),
            'protocolInteractionCount': contract_metrics.get('protocolInteractionCount', 0),
            'totalDeFiBalanceUSD': contract_metrics.get('totalDeFiBalanceUSD', 0),
            'liquidityPositionCount': contract_metrics.get('liquidityPositionCount', 0),
            'protocolDiversityScore': contract_metrics.get('protocolDiversityScore', 0),
            'interactionDepthScore': contract_metrics.get('interactionDepthScore', 0),
            'yieldFarmingActive': contract_metrics.get('yieldFarmingActive', 0),
            'totalStakedUSD': contract_metrics.get('totalStakedUSD', 0),
            'stakingDurationDays': contract_metrics.get('stakingDurationDays', 0),
            'stakingPlatformCount': contract_metrics.get('stakingPlatformCount', 0),
            'rewardClaimFrequency': contract_metrics.get('rewardClaimFrequency', 0),
            'stakingLoyaltyScore': contract_metrics.get('stakingLoyaltyScore', 0),
            'platformDiversityScore': contract_metrics.get('platformDiversityScore', 0),
            'liquidationEventCount': contract_metrics.get('liquidationEventCount', 0),
            'leverageRatio': contract_metrics.get('leverageRatio', 100),
            'portfolioVolatility': contract_metrics.get('portfolioVolatility', 50),
            'riskScore': contract_metrics.get('riskScore', 50),
            'accountAge': contract_metrics.get('accountAge', 0),
            'lastActivityDays': contract_metrics.get('lastActivityDays', 0),
            'engagementScore': contract_metrics.get('engagementScore', 50),
            'dataQuality': processing_metadata.get('data_quality', {}).get('quality_score', 50)
        }

# Test implementation
async def test_data_processor():
    """Test the data processor with a known address"""
    
    processor = DataProcessor()
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    try:
        print("🧪 Testing Data Processor...")
        print("=" * 50)
        
        # Test processing
        contract_metrics, metadata = await processor.process_user_behavioral_data(test_address)
        
        print(f"✅ Processing completed for: {test_address}")
        print(f"✅ Contract metrics count: {len(contract_metrics)}")
        print(f"✅ Total score preview: {sum(contract_metrics.values())}")
        print(f"✅ Data quality: {metadata['data_quality']['quality_score']}/100")
        print(f"✅ Processing status: {metadata['processing_status']}")
        
        # Test validation
        validation = processor.validate_contract_format(contract_metrics)
        print(f"✅ Format validation: {'PASS' if validation['is_valid'] else 'FAIL'}")
        
        if not validation['is_valid']:
            print("❌ Validation issues:")
            for issue in validation['issues']:
                print(f"   - {issue}")
        
        # Preview functionality
        preview = await processor.preview_contract_data(test_address)
        print(f"✅ Preview generated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processor test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_data_processor())
