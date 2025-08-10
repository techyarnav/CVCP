# clients/multi_chain_aggregator.py
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import os
import json
from datetime import datetime
from loguru import logger

from .alchemy_client import AlchemyClient
from .zapper_client import ZapperClient
from .moralis_client import MoralisClient

class MultiChainDataAggregator:
    """
    Complete multi-chain data aggregator orchestrating all API sources
    Coordinates: Alchemy (transactions), Zapper (DeFi), Moralis (staking)
    """
    
    def __init__(self):
        # Initialize all API clients with enhanced error handling
        self.clients = {}
        self.client_status = {}
        
        try:
            self.clients['alchemy'] = AlchemyClient()
            self.client_status['alchemy'] = 'ready'
            logger.info("✅ Alchemy client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Alchemy client: {e}")
            self.clients['alchemy'] = None
            self.client_status['alchemy'] = f'failed: {str(e)}'
        
        try:
            self.clients['zapper'] = ZapperClient()
            self.client_status['zapper'] = 'ready'
            logger.info("✅ Zapper client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Zapper client: {e}")
            self.clients['zapper'] = None
            self.client_status['zapper'] = f'failed: {str(e)}'
        
        try:
            self.clients['moralis'] = MoralisClient()
            self.client_status['moralis'] = 'ready'
            logger.info("✅ Moralis client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Moralis client: {e}")
            self.clients['moralis'] = None
            self.client_status['moralis'] = f'failed: {str(e)}'
        
        # Configuration
        self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', 3))
        self.individual_client_timeout = 20  # New: timeout per client

        self.request_timeout = 60  # Extended timeout for comprehensive data collection
        self.max_retries = 2
        self.retry_delay = 1
    
    async def fetch_user_comprehensive_data(self, address: str) -> Dict[str, Any]:
        """
        Fetch comprehensive user data from all sources with enhanced error handling and retry logic
        """
        logger.info(f"🚀 Starting comprehensive data collection for address: {address}")
        
        start_time = datetime.now()
        
        try:
            # Validate address format
            if not self._is_valid_address(address):
                raise ValueError(f"Invalid Ethereum address format: {address}")
            
            # Execute data collection from all sources with retry logic
            collection_results = await self._collect_all_data_with_comprehensive_retry(address)
            
            # Process and structure the collected data
            structured_data = self._structure_comprehensive_data(address, collection_results, start_time)
            
            # Calculate data quality and completeness scores
            structured_data['data_quality_analysis'] = self._calculate_comprehensive_data_quality(collection_results)
            
            # Add aggregation metadata
            structured_data['aggregation_metadata'] = self._generate_aggregation_metadata(collection_results, start_time)
            
            collection_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Data collection completed in {collection_time:.2f} seconds for {address}")
            
            return structured_data
            
        except Exception as e:
            logger.error(f"❌ Error in comprehensive data collection for {address}: {str(e)}")
            return self._get_empty_comprehensive_data(address, start_time, str(e))
    
    async def _collect_all_data_with_comprehensive_retry(self, address: str) -> Dict[str, Any]:
        """Enhanced data collection with comprehensive retry logic and parallel processing"""
        
        # Prepare collection tasks with retry logic
        collection_tasks = []
        
        if self.clients['alchemy']:
            collection_tasks.append(
                self._collect_data_with_retry('alchemy', address, self.clients['alchemy'].get_transaction_metrics)
            )
        
        if self.clients['zapper']:
            collection_tasks.append(
                self._collect_data_with_retry('zapper', address, self.clients['zapper'].get_defi_metrics)
            )
        
        if self.clients['moralis']:
            collection_tasks.append(
                self._collect_data_with_retry('moralis', address, self.clients['moralis'].get_staking_metrics)
            )
        
        if not collection_tasks:
            logger.error("❌ No API clients available for data collection")
            return {
                'alchemy': {'success': False, 'data': {}, 'error': 'Client not available', 'attempts': 0},
                'zapper': {'success': False, 'data': {}, 'error': 'Client not available', 'attempts': 0},
                'moralis': {'success': False, 'data': {}, 'error': 'Client not available', 'attempts': 0}
            }
        
        # Execute all tasks with comprehensive timeout protection
        try:
            logger.info(f"🔄 Executing {len(collection_tasks)} data collection tasks...")
            
            results = await asyncio.wait_for(
                asyncio.gather(*collection_tasks, return_exceptions=True),
                timeout=self.request_timeout
            )
            
            # Process results
            collection_results = {}
            task_names = []
            
            # Determine task names based on available clients
            if self.clients['alchemy']:
                task_names.append('alchemy')
            if self.clients['zapper']:
                task_names.append('zapper')
            if self.clients['moralis']:
                task_names.append('moralis')
            
            for i, (task_name, result) in enumerate(zip(task_names, results)):
                if isinstance(result, Exception):
                    logger.error(f"❌ {task_name} collection failed with exception: {str(result)}")
                    collection_results[task_name] = {
                        'success': False,
                        'data': {},
                        'error': str(result),
                        'attempts': self.max_retries,
                        'collection_time': 0
                    }
                else:
                    collection_results[task_name] = result
            
            # Ensure all expected keys exist
            for source in ['alchemy', 'zapper', 'moralis']:
                if source not in collection_results:
                    collection_results[source] = {
                        'success': False,
                        'data': {},
                        'error': 'Client not initialized or task not executed',
                        'attempts': 0,
                        'collection_time': 0
                    }
            
            return collection_results
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Data collection timeout after {self.request_timeout} seconds")
            return {
                'alchemy': {'success': False, 'data': {}, 'error': 'Global timeout', 'attempts': 0, 'collection_time': self.request_timeout},
                'zapper': {'success': False, 'data': {}, 'error': 'Global timeout', 'attempts': 0, 'collection_time': self.request_timeout},
                'moralis': {'success': False, 'data': {}, 'error': 'Global timeout', 'attempts': 0, 'collection_time': self.request_timeout}
            }
    

    def _is_valid_address(self, address: str) -> bool:
        """Check if the given string is a valid Ethereum-like address."""
        return (
            isinstance(address, str)
            and address.startswith('0x')
            and len(address) == 42
            and all(c in '0123456789abcdefABCDEF' for c in address[2:])
        )

    def _get_empty_comprehensive_data(
        self, address: str, start_time, error: str = None
    ) -> dict:
        """Return a standard empty data structure when collection fails."""
        return {
            'address': address.lower() if isinstance(address, str) else address,
            'collection_timestamp': start_time.timestamp() if start_time else None,
            'collection_date': start_time.isoformat() if start_time else None,
            'collection_duration_seconds': None,
            'error': error,
            'raw_data': {
                'alchemy': {},
                'zapper': {},
                'moralis': {}
            },
            'structured_metrics': {
                'transaction_metrics': {},
                'defi_metrics': {},
                'staking_metrics': {}
            },
            'collection_status': {
                'alchemy': {'success': False, 'attempts': 0, 'collection_time': 0, 'error': error},
                'zapper': {'success': False, 'attempts': 0, 'collection_time': 0, 'error': error},
                'moralis': {'success': False, 'attempts': 0, 'collection_time': 0, 'error': error}
            },
            'user_analytics': {},
            'data_correlations': {},
            'summary_statistics': {},
            'data_quality_analysis': {
                'overall_quality_score': 0,
                'completeness_percentage': 0,
                'quality_grade': 'F'
            }
        }
    async def _collect_data_with_retry(self, source_name: str, address: str, collection_func) -> dict:
        """Enhanced data collection with retry logic and timeout handling."""
        start_time = datetime.now()
        max_retries = 3
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 {source_name} attempt {attempt + 1}/{max_retries}")

                # Use timeout of 60 seconds for each attempt
                result = await asyncio.wait_for(
                    collection_func(address),
                    timeout=60
                )

                collection_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ {source_name} collection successful in {collection_time:.2f}s")

                return {
                    'success': True,
                    'data': result,
                    'error': None,
                    'attempts': attempt + 1,
                    'collection_time': collection_time
                }
            except asyncio.TimeoutError:
                collection_time = (datetime.now() - start_time).total_seconds()
                logger.warning(f"⏰ {source_name} attempt {attempt + 1} timed out after {collection_time:.2f}s")

                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'data': {},
                        'error': f'{source_name} timeout after {max_retries} attempts',
                        'attempts': max_retries,
                        'collection_time': collection_time
                    }
                await asyncio.sleep(retry_delay)
            except Exception as e:
                collection_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"❌ {source_name} attempt {attempt + 1} error: {str(e)}")

                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'data': {},
                        'error': str(e),
                        'attempts': max_retries,
                        'collection_time': collection_time
                    }
                await asyncio.sleep(retry_delay)
         
    def _structure_comprehensive_data(self, address: str, collection_results: Dict, 
                                    start_time: datetime) -> Dict[str, Any]:
        """Structure all collected data into comprehensive format with enhanced analytics"""
        
        # Extract data from each source
        alchemy_data = collection_results.get('alchemy', {}).get('data', {})
        zapper_data = collection_results.get('zapper', {}).get('data', {})
        moralis_data = collection_results.get('moralis', {}).get('data', {})
        
        # Structure the comprehensive data
        comprehensive_data = {
            'address': address.lower(),
            'collection_timestamp': start_time.timestamp(),
            'collection_date': start_time.isoformat(),
            'collection_duration_seconds': (datetime.now() - start_time).total_seconds(),
            
            # Raw data from each source (for debugging and analysis)
            'raw_data': {
                'alchemy': alchemy_data,
                'zapper': zapper_data,
                'moralis': moralis_data
            },
            
            # Structured metrics for smart contract consumption
            'structured_metrics': {
                'transaction_metrics': self._extract_enhanced_transaction_metrics(alchemy_data),
                'defi_metrics': self._extract_enhanced_defi_metrics(zapper_data),
                'staking_metrics': self._extract_enhanced_staking_metrics(moralis_data)
            },
            
            # Collection status and performance
            'collection_status': {
                'alchemy': {
                    'success': collection_results.get('alchemy', {}).get('success', False),
                    'attempts': collection_results.get('alchemy', {}).get('attempts', 0),
                    'collection_time': collection_results.get('alchemy', {}).get('collection_time', 0),
                    'error': collection_results.get('alchemy', {}).get('error')
                },
                'zapper': {
                    'success': collection_results.get('zapper', {}).get('success', False),
                    'attempts': collection_results.get('zapper', {}).get('attempts', 0),
                    'collection_time': collection_results.get('zapper', {}).get('collection_time', 0),
                    'error': collection_results.get('zapper', {}).get('error')
                },
                'moralis': {
                    'success': collection_results.get('moralis', {}).get('success', False),
                    'attempts': collection_results.get('moralis', {}).get('attempts', 0),
                    'collection_time': collection_results.get('moralis', {}).get('collection_time', 0),
                    'error': collection_results.get('moralis', {}).get('error')
                }
            },
            
            # Enhanced analytics and insights
            'user_analytics': self._calculate_comprehensive_user_analytics(alchemy_data, zapper_data, moralis_data),
            
            # Cross-source data correlations
            'data_correlations': self._calculate_data_correlations(alchemy_data, zapper_data, moralis_data),
            
            # Summary statistics
            'summary_statistics': self._calculate_enhanced_summary_statistics(alchemy_data, zapper_data, moralis_data)
        }
        
        return comprehensive_data
    
    def _extract_enhanced_transaction_metrics(self, alchemy_data: Dict) -> Dict[str, Any]:
        """Extract and normalize enhanced transaction metrics for smart contract"""
        
        if not alchemy_data:
            return self._get_empty_transaction_metrics()
        
        return {
            # Core metrics (smart contract compatible)
            'transactionFrequency': int(alchemy_data.get('monthly_txn_count', 0)),
            'averageTransactionValue': int(alchemy_data.get('avg_value_usd', 0)),
            'gasEfficiencyScore': int(alchemy_data.get('gas_efficiency', 50)),
            'crossChainActivityCount': int(alchemy_data.get('active_chains', 0)),
            'consistencyMetric': int(alchemy_data.get('consistency_score', 0)),
            
            # Enhanced metrics
            'totalTransactions': int(alchemy_data.get('total_transactions', 0)),
            'weeklyTransactionCount': int(alchemy_data.get('weekly_txn_count', 0)),
            'dailyAverageTransactions': float(alchemy_data.get('daily_avg_txns', 0)),
            'medianTransactionValue': float(alchemy_data.get('median_value_usd', 0)),
            'totalVolumeUSD': float(alchemy_data.get('total_volume_usd', 0)),
            'activityScore': int(alchemy_data.get('activity_score', 0)),
            'crossChainScore': int(alchemy_data.get('cross_chain_score', 0)),
            
            # Activity patterns
            'activityTrend': alchemy_data.get('recent_activity', {}).get('trend', 'unknown'),
            'isActiveUser': alchemy_data.get('recent_activity', {}).get('is_active_user', False),
            'transactionTypes': alchemy_data.get('transaction_types', {}),
            
            # Data quality
            'dataQualityScore': int(alchemy_data.get('data_quality_score', 0)),
            'successfulChains': alchemy_data.get('successful_chains', []),
            'failedChains': alchemy_data.get('failed_chains', [])
        }
    
    def _extract_enhanced_defi_metrics(self, zapper_data: Dict) -> Dict[str, Any]:
        """Extract and normalize enhanced DeFi metrics for smart contract"""
        
        if not zapper_data:
            return self._get_empty_defi_metrics()
        
        return {
            # Core metrics (smart contract compatible)
            'protocolInteractionCount': int(zapper_data.get('unique_protocols', 0)),
            'totalDeFiBalanceUSD': int(zapper_data.get('total_balance_usd', 0)),
            'liquidityPositionCount': int(zapper_data.get('lp_positions', 0)),
            'protocolDiversityScore': int(zapper_data.get('diversity_score', 0)),
            'interactionDepthScore': int(zapper_data.get('interaction_depth', 0)),
            'yieldFarmingActive': int(zapper_data.get('yield_analysis', {}).get('active_farming', False)),
            
            # Enhanced metrics
            'sophisticationScore': int(zapper_data.get('sophistication_score', 0)),
            'experienceLevel': zapper_data.get('defi_experience_level', 'newcomer'),
            'totalLiquidityProvisionValue': float(zapper_data.get('liquidity_analysis', {}).get('total_lp_value_usd', 0)),
            'yieldFarmingValue': float(zapper_data.get('yield_analysis', {}).get('total_farming_value_usd', 0)),
            'portfolioDiversity': int(zapper_data.get('portfolio_analysis', {}).get('portfolio_diversity', 0)),
            
            # Risk analysis
            'riskScore': float(zapper_data.get('risk_analysis', {}).get('risk_score', 0)),
            'riskLevel': zapper_data.get('risk_analysis', {}).get('risk_level', 'unknown'),
            
            # Protocol analytics
            'protocolCategories': zapper_data.get('protocol_analysis', {}).get('protocol_categories', {}),
            'networkDistribution': zapper_data.get('network_analysis', {}).get('networks_used', []),
            'crossNetworkScore': int(zapper_data.get('network_analysis', {}).get('cross_network_score', 0)),
            
            # Data quality
            'dataQualityScore': int(zapper_data.get('data_quality_score', 0))
        }
    
    def _extract_enhanced_staking_metrics(self, moralis_data: Dict) -> Dict[str, Any]:
        """Extract and normalize enhanced staking metrics for smart contract"""
        
        if not moralis_data:
            return self._get_empty_staking_metrics()
        
        return {
            # Core metrics (smart contract compatible)
            'totalStakedUSD': int(moralis_data.get('total_staked_usd', 0)),
            'stakingDurationDays': int(moralis_data.get('avg_duration_days', 0)),
            'stakingPlatformCount': int(moralis_data.get('platform_count', 0)),
            'rewardClaimFrequency': int(moralis_data.get('claim_frequency', 0)),
            'stakingLoyaltyScore': int(moralis_data.get('staking_loyalty_score', 0)),
            'platformDiversityScore': int(moralis_data.get('platform_diversity', 0)),
            
            # Enhanced metrics
            'sophisticationScore': int(moralis_data.get('sophistication_score', 0)),
            'experienceLevel': moralis_data.get('staking_experience_level', 'newcomer'),
            'estimatedAnnualRewards': float(moralis_data.get('estimated_annual_rewards_usd', 0)),
            'positionStability': moralis_data.get('behavior_analysis', {}).get('position_stability', 'unknown'),
            'rewardOptimizationScore': int(moralis_data.get('behavior_analysis', {}).get('reward_optimization_score', 0)),
            
            # Platform analysis
            'dominantPlatform': moralis_data.get('platform_analysis', {}).get('dominant_platform', ''),
            'platformConcentrationRatio': float(moralis_data.get('platform_analysis', {}).get('platform_concentration_ratio', 0)),
            'diversificationLevel': moralis_data.get('platform_analysis', {}).get('diversification_level', 'none'),
            
            # Risk analysis
            'riskLevel': moralis_data.get('risk_analysis', {}).get('risk_level', 'unknown'),
            'overallRiskScore': float(moralis_data.get('risk_analysis', {}).get('overall_risk_score', 0)),
            
            # Staking specifics
            'uniqueStakingTokens': int(moralis_data.get('staking_token_analysis', {}).get('unique_staking_tokens', 0)),
            'stakingProtocols': moralis_data.get('staking_token_analysis', {}).get('staking_protocols', []),
            
            # Data quality
            'dataQualityScore': int(moralis_data.get('data_quality_score', 0))
        }
    
    def _calculate_comprehensive_user_analytics(self, alchemy_data: Dict, zapper_data: Dict, moralis_data: Dict) -> Dict[str, Any]:
        """Calculate comprehensive user analytics across all data sources"""
        
        # Total portfolio value calculation
        defi_value = zapper_data.get('total_balance_usd', 0) if zapper_data else 0
        staking_value = moralis_data.get('total_staked_usd', 0) if moralis_data else 0
        total_portfolio_value = defi_value + staking_value
        
        # Activity scoring
        tx_activity = alchemy_data.get('monthly_txn_count', 0) if alchemy_data else 0
        defi_activity = zapper_data.get('unique_protocols', 0) if zapper_data else 0
        staking_activity = moralis_data.get('platform_count', 0) if moralis_data else 0
        
        overall_activity_score = min(100, (tx_activity * 2) + (defi_activity * 5) + (staking_activity * 10))
        
        # Sophistication analysis
        defi_sophistication = zapper_data.get('sophistication_score', 0) if zapper_data else 0
        staking_sophistication = moralis_data.get('sophistication_score', 0) if moralis_data else 0
        overall_sophistication = (defi_sophistication + staking_sophistication) / 2
        
        # Risk profile
        defi_risk = zapper_data.get('risk_analysis', {}).get('risk_score', 0) if zapper_data else 0
        staking_risk = moralis_data.get('risk_analysis', {}).get('overall_risk_score', 0) if moralis_data else 0
        overall_risk_score = (defi_risk + staking_risk) / 2
        
        # User categorization
        user_category = self._categorize_user_profile(
            total_portfolio_value, overall_activity_score, overall_sophistication, tx_activity, defi_activity, staking_activity
        )
        
        return {
            'total_portfolio_value_usd': total_portfolio_value,
            'defi_portfolio_value': defi_value,
            'staking_portfolio_value': staking_value,
            'portfolio_allocation': {
                'defi_percentage': (defi_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0,
                'staking_percentage': (staking_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            },
            'overall_activity_score': overall_activity_score,
            'overall_sophistication_score': overall_sophistication,
            'overall_risk_score': overall_risk_score,
            'user_category': user_category,
            'engagement_metrics': {
                'transaction_engagement': self._calculate_engagement_level(tx_activity),
                'defi_engagement': self._calculate_engagement_level(defi_activity * 2),
                'staking_engagement': self._calculate_engagement_level(staking_activity * 5)
            }
        }
    
    def _calculate_data_correlations(self, alchemy_data: Dict, zapper_data: Dict, moralis_data: Dict) -> Dict[str, Any]:
        """Calculate correlations between different data sources"""
        
        correlations = {}
        
        # Transaction vs DeFi correlation
        if alchemy_data and zapper_data:
            tx_activity = alchemy_data.get('monthly_txn_count', 0)
            defi_protocols = zapper_data.get('unique_protocols', 0)
            
            # Simple correlation: more transactions usually correlate with more DeFi usage
            if tx_activity > 0 and defi_protocols > 0:
                tx_defi_ratio = min(5, defi_protocols / (tx_activity / 10))  # Normalize
                correlations['transaction_defi_correlation'] = tx_defi_ratio
            else:
                correlations['transaction_defi_correlation'] = 0
        
        # DeFi vs Staking correlation
        if zapper_data and moralis_data:
            defi_value = zapper_data.get('total_balance_usd', 0)
            staking_value = moralis_data.get('total_staked_usd', 0)
            
            if defi_value > 0 or staking_value > 0:
                total_value = defi_value + staking_value
                defi_ratio = defi_value / total_value
                staking_ratio = staking_value / total_value
                
                correlations['defi_staking_balance'] = {
                    'defi_dominance': defi_ratio,
                    'staking_dominance': staking_ratio,
                    'balance_type': 'defi_focused' if defi_ratio > 0.7 else 'staking_focused' if staking_ratio > 0.7 else 'balanced'
                }
        
        # Cross-chain activity correlation
        chains_active = alchemy_data.get('active_chains', 0) if alchemy_data else 0
        defi_networks = len(zapper_data.get('network_analysis', {}).get('networks_used', [])) if zapper_data else 0
        
        correlations['cross_chain_consistency'] = {
            'alchemy_chains': chains_active,
            'defi_networks': defi_networks,
            'consistency_score': min(100, abs(chains_active - defi_networks) * 20) if chains_active > 0 or defi_networks > 0 else 0
        }
        
        return correlations
    
    def _calculate_enhanced_summary_statistics(self, alchemy_data: Dict, zapper_data: Dict, moralis_data: Dict) -> Dict[str, Any]:
        """Calculate enhanced summary statistics across all data sources"""
        
        return {
            # Data availability summary
            'data_sources_available': sum([
                1 if alchemy_data else 0,
                1 if zapper_data else 0,
                1 if moralis_data else 0
            ]),
            'data_completeness_percentage': (sum([
                1 if alchemy_data else 0,
                1 if zapper_data else 0,
                1 if moralis_data else 0
            ]) / 3) * 100,
            
            # Key metrics summary
            'key_metrics': {
                'monthly_transactions': alchemy_data.get('monthly_txn_count', 0) if alchemy_data else 0,
                'active_chains': alchemy_data.get('active_chains', 0) if alchemy_data else 0,
                'defi_protocols': zapper_data.get('unique_protocols', 0) if zapper_data else 0,
                'defi_balance_usd': zapper_data.get('total_balance_usd', 0) if zapper_data else 0,
                'staking_platforms': moralis_data.get('platform_count', 0) if moralis_data else 0,
                'staking_balance_usd': moralis_data.get('total_staked_usd', 0) if moralis_data else 0
            },
            
            # Experience levels
            'experience_levels': {
                'defi_experience': zapper_data.get('defi_experience_level', 'newcomer') if zapper_data else 'newcomer',
                'staking_experience': moralis_data.get('staking_experience_level', 'newcomer') if moralis_data else 'newcomer'
            },
            
            # Activity patterns
            'activity_patterns': {
                'transaction_trend': alchemy_data.get('recent_activity', {}).get('trend', 'unknown') if alchemy_data else 'unknown',
                'is_defi_active': (zapper_data.get('unique_protocols', 0) > 0) if zapper_data else False,
                'is_staking_active': (moralis_data.get('total_staked_usd', 0) > 0) if moralis_data else False
            },
            
            # Risk assessment
            'risk_summary': {
                'defi_risk_level': zapper_data.get('risk_analysis', {}).get('risk_level', 'unknown') if zapper_data else 'unknown',
                'staking_risk_level': moralis_data.get('risk_analysis', {}).get('risk_level', 'unknown') if moralis_data else 'unknown',
                'overall_risk_assessment': self._assess_overall_risk(alchemy_data, zapper_data, moralis_data)
            }
        }
    
    def _calculate_comprehensive_data_quality(self, collection_results: Dict) -> Dict[str, Any]:
        """Calculate comprehensive data quality across all sources"""
        
        source_quality = {}
        total_quality = 0
        successful_sources = 0
        total_collection_time = 0
        
        for source, result in collection_results.items():
            if result.get('success', False):
                data_quality = result.get('data', {}).get('data_quality_score', 0)
                source_quality[source] = {
                    'quality_score': data_quality,
                    'collection_time': result.get('collection_time', 0),
                    'attempts': result.get('attempts', 0),
                    'status': 'success'
                }
                total_quality += data_quality
                successful_sources += 1
            else:
                source_quality[source] = {
                    'quality_score': 0,
                    'collection_time': result.get('collection_time', 0),
                    'attempts': result.get('attempts', 0),
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error')
                }
            
            total_collection_time += result.get('collection_time', 0)
        
        overall_quality = total_quality / max(1, successful_sources)
        completeness = (successful_sources / 3) * 100  # 3 total sources
        
        return {
            'overall_quality_score': int(overall_quality),
            'completeness_percentage': int(completeness),
            'successful_sources': successful_sources,
            'total_sources': 3,
            'total_collection_time': round(total_collection_time, 2),
            'average_collection_time': round(total_collection_time / 3, 2),
            'source_quality_breakdown': source_quality,
            'quality_grade': self._get_quality_grade(overall_quality, completeness),
            'performance_rating': self._get_performance_rating(total_collection_time, successful_sources)
        }
    
    def _generate_aggregation_metadata(self, collection_results: Dict, start_time: datetime) -> Dict[str, Any]:
        """Generate comprehensive metadata about the aggregation process"""
        
        return {
            'aggregation_version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'total_duration_seconds': (datetime.now() - start_time).total_seconds(),
            'client_status': self.client_status,
            'collection_configuration': {
                'max_concurrent_requests': self.max_concurrent_requests,
                'request_timeout': self.request_timeout,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay
            },
            'retry_statistics': {
                source: {
                    'attempts': result.get('attempts', 0),
                    'success': result.get('success', False),
                    'collection_time': result.get('collection_time', 0)
                }
                for source, result in collection_results.items()
            }
        }
    
    # Helper methods
    def _categorize_user_profile(self, portfolio_value: float, activity_score: int, sophistication: float,
                               tx_activity: int, defi_activity: int, staking_activity: int) -> str:
        """Categorize user profile based on comprehensive metrics"""
        
        if portfolio_value > 100000 and activity_score > 80 and sophistication > 80:
            return 'whale_power_user'
        elif portfolio_value > 50000 and activity_score > 60 and sophistication > 60:
            return 'advanced_defi_user'
        elif portfolio_value > 10000 and defi_activity > 5:
            return 'active_defi_user'
        elif staking_activity > 2 and portfolio_value > 5000:
            return 'staking_focused_user'
        elif tx_activity > 10 and portfolio_value > 1000:
            return 'active_crypto_user'
        elif portfolio_value > 100:
            return 'casual_user'
        else:
            return 'newcomer'
    
    def _calculate_engagement_level(self, activity_metric: int) -> str:
        """Calculate engagement level based on activity metric"""
        
        if activity_metric > 50:
            return 'very_high'
        elif activity_metric > 20:
            return 'high'
        elif activity_metric > 10:
            return 'medium'
        elif activity_metric > 0:
            return 'low'
        else:
            return 'none'
    
    def _assess_overall_risk(self, alchemy_data: Dict, zapper_data: Dict, moralis_data: Dict) -> str:
        """Assess overall risk level across all activities"""
        
        risk_factors = []
        
        # Transaction risk (high frequency might indicate trading)
        if alchemy_data:
            tx_frequency = alchemy_data.get('monthly_txn_count', 0)
            if tx_frequency > 100:
                risk_factors.append('high_transaction_frequency')
        
        # DeFi risk
        if zapper_data:
            defi_risk = zapper_data.get('risk_analysis', {}).get('risk_level', 'unknown')
            if defi_risk == 'high':
                risk_factors.append('high_defi_risk')
        
        # Staking risk
        if moralis_data:
            staking_risk = moralis_data.get('risk_analysis', {}).get('risk_level', 'unknown')
            if staking_risk == 'high':
                risk_factors.append('high_staking_risk')
        
        # Overall assessment
        if len(risk_factors) >= 2:
            return 'high'
        elif len(risk_factors) == 1:
            return 'medium'
        else:
            return 'low'
    
    def _get_quality_grade(self, quality_score: float, completeness: float) -> str:
        """Assign quality grade based on score and completeness"""
        
        combined_score = (quality_score * 0.7) + (completeness * 0.3)
        
        if combined_score >= 90:
            return 'A+'
        elif combined_score >= 85:
            return 'A'
        elif combined_score >= 80:
            return 'B+'
        elif combined_score >= 75:
            return 'B'
        elif combined_score >= 70:
            return 'C+'
        elif combined_score >= 60:
            return 'C'
        elif combined_score >= 50:
            return 'D'
        else:
            return 'F'
    
    def _get_performance_rating(self, total_time: float, successful_sources: int) -> str:
        """Rate performance based on collection time and success rate"""
        
        if successful_sources == 3 and total_time < 30:
            return 'excellent'
        elif successful_sources >= 2 and total_time < 60:
            return 'good'
        elif successful_sources >= 2 and total_time < 120:
            return 'fair'
        elif successful_sources >= 1:
            return 'poor'
        else:
            return 'failed'
    
    def _is_valid_address(self, address: str) -> bool:
        """Enhanced address validation"""
        return (
            isinstance(address, str) and
            address.startswith('0x') and
            len(address) == 42 and
            all(c in '0123456789abcdefABCDEF' for c in address[2:])
        )
    
    def _get_empty_comprehensive_data(self, address: str, start_time: datetime, error: str = None) -> Dict[str, Any]:
        """Return comprehensive empty data structure"""
        return {
            'address': address.lower(),
            'collection_timestamp': start_time.timestamp(),
            'collection_date': start_time.isoformat(),
            'collection_duration_seconds': (datetime.now() - start_time).total_seconds(),
            'error': error,
            'raw_data': {
                'alchemy': {},
                'zapper': {},
                'moralis': {}
            },
            'structured_metrics': {
                'transaction_metrics': self._get_empty_transaction_metrics(),
                'defi_metrics': self._get_empty_defi_metrics(),
                'staking_metrics': self._get_empty_staking_metrics()
            },
            'collection_status': {
                'alchemy': {'success': False, 'attempts': 0, 'collection_time': 0, 'error': error},
                'zapper': {'success': False, 'attempts': 0, 'collection_time': 0, 'error': error},
                'moralis': {'success': False, 'attempts': 0, 'collection_time': 0, 'error': error}
            },
            'user_analytics': {
                'total_portfolio_value_usd': 0,
                'overall_activity_score': 0,
                'overall_sophistication_score': 0,
                'user_category': 'error'
            },
            'data_correlations': {},
            'summary_statistics': {
                'data_sources_available': 0,
                'data_completeness_percentage': 0
            },
            'data_quality_analysis': {
                'overall_quality_score': 0,
                'completeness_percentage': 0,
                'quality_grade': 'F'
            }
        }
    
    # Empty metrics methods
    def _get_empty_transaction_metrics(self) -> Dict[str, Any]:
        """Return empty transaction metrics"""
        return {
            'transactionFrequency': 0,
            'averageTransactionValue': 0,
            'gasEfficiencyScore': 50,
            'crossChainActivityCount': 0,
            'consistencyMetric': 0,
            'totalTransactions': 0,
            'dataQualityScore': 0
        }
    
    def _get_empty_defi_metrics(self) -> Dict[str, Any]:
        """Return empty DeFi metrics"""
        return {
            'protocolInteractionCount': 0,
            'totalDeFiBalanceUSD': 0,
            'liquidityPositionCount': 0,
            'protocolDiversityScore': 0,
            'interactionDepthScore': 0,
            'yieldFarmingActive': 0,
            'dataQualityScore': 0
        }
    
    def _get_empty_staking_metrics(self) -> Dict[str, Any]:
        """Return empty staking metrics"""
        return {
            'totalStakedUSD': 0,
            'stakingDurationDays': 0,
            'stakingPlatformCount': 0,
            'rewardClaimFrequency': 0,
            'stakingLoyaltyScore': 0,
            'platformDiversityScore': 0,
            'dataQualityScore': 0
        }

# Test implementation
async def test_complete_multi_chain_aggregator():
    """Comprehensive test for the complete multi-chain aggregator"""
    
    aggregator = MultiChainDataAggregator()
    
    # Test addresses
    test_addresses = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
        "0x742d35Cc6654c967e5c749CB1b5B43cA2E9b0b70"   # Another test address
    ]
    
    print("🚀 Testing Complete Multi-Chain Data Aggregator")
    print("=" * 70)
    
    for i, address in enumerate(test_addresses, 1):
        print(f"\n📊 Test {i}: Processing address {address}")
        print("-" * 50)
        
        try:
            comprehensive_data = await aggregator.fetch_user_comprehensive_data(address)
            
            # Display results
            print(f"✅ Address: {comprehensive_data['address']}")
            print(f"✅ Collection Time: {comprehensive_data['collection_duration_seconds']:.2f}s")
            print(f"✅ Data Quality Grade: {comprehensive_data['data_quality_analysis']['quality_grade']}")
            print(f"✅ Completeness: {comprehensive_data['data_quality_analysis']['completeness_percentage']}%")
            print(f"✅ User Category: {comprehensive_data['user_analytics']['user_category']}")
            
            # Summary metrics
            tx_metrics = comprehensive_data['structured_metrics']['transaction_metrics']
            defi_metrics = comprehensive_data['structured_metrics']['defi_metrics']
            staking_metrics = comprehensive_data['structured_metrics']['staking_metrics']
            
            print(f"\n🔄 Transaction Activity:")
            print(f"  - Monthly Transactions: {tx_metrics['transactionFrequency']}")
            print(f"  - Cross-Chain Activity: {tx_metrics['crossChainActivityCount']} chains")
            print(f"  - Gas Efficiency: {tx_metrics['gasEfficiencyScore']}%")
            
            print(f"\n🏦 DeFi Engagement:")
            print(f"  - Unique Protocols: {defi_metrics['protocolInteractionCount']}")
            print(f"  - Total Balance: ${defi_metrics['totalDeFiBalanceUSD']:,}")
            print(f"  - Experience Level: {defi_metrics['experienceLevel']}")
            
            print(f"\n🥩 Staking Activity:")
            print(f"  - Total Staked: ${staking_metrics['totalStakedUSD']:,}")
            print(f"  - Platform Count: {staking_metrics['stakingPlatformCount']}")
            print(f"  - Experience Level: {staking_metrics['experienceLevel']}")
            
            print(f"\n📈 Overall Analytics:")
            print(f"  - Portfolio Value: ${comprehensive_data['user_analytics']['total_portfolio_value_usd']:,}")
            print(f"  - Activity Score: {comprehensive_data['user_analytics']['overall_activity_score']}/100")
            print(f"  - Sophistication Score: {comprehensive_data['user_analytics']['overall_sophistication_score']:.1f}/100")
            
        except Exception as e:
            print(f"❌ Error processing {address}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Multi-Chain Aggregator Testing Completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_complete_multi_chain_aggregator())
