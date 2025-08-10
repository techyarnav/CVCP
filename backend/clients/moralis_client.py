# clients/moralis_client.py
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import os
import json
from loguru import logger
from datetime import datetime, timedelta

class MoralisClient:
    """
    Complete and robust Moralis API client for staking data and portfolio analytics
    FREE alternative to DeBank with comprehensive staking analysis
    """
    
    def __init__(self):
        self.api_key = os.getenv('MORALIS_API_KEY')
        self.base_url = 'https://deep-index.moralis.io/api/v2.2'
        self.headers = {
            'accept': 'application/json',
            'X-API-Key': self.api_key
        } if self.api_key else {}
        
        # Enhanced staking protocol mapping
        self.staking_protocols = {
            'lido': {
                'name': 'Lido Finance',
                'tokens': ['stETH', 'wstETH'],
                'category': 'liquid_staking',
                'risk_level': 'low'
            },
            'rocket-pool': {
                'name': 'Rocket Pool', 
                'tokens': ['rETH', 'RPL'],
                'category': 'decentralized_staking',
                'risk_level': 'medium'
            },
            'stakewise': {
                'name': 'StakeWise',
                'tokens': ['sETH2', 'rETH2'],
                'category': 'liquid_staking',
                'risk_level': 'medium'
            },
            'frax': {
                'name': 'Frax Finance',
                'tokens': ['sfrxETH', 'frxETH'],
                'category': 'algorithmic_staking',
                'risk_level': 'medium'
            }
        }
        
        # Known staking tokens with metadata
        self.staking_tokens = {
            'stETH': {
                'protocol': 'lido',
                'underlying': 'ETH',
                'type': 'liquid_staking',
                'apy_estimate': 4.5
            },
            'wstETH': {
                'protocol': 'lido',
                'underlying': 'ETH', 
                'type': 'wrapped_liquid_staking',
                'apy_estimate': 4.5
            },
            'rETH': {
                'protocol': 'rocket-pool',
                'underlying': 'ETH',
                'type': 'liquid_staking',
                'apy_estimate': 4.2
            },
            'cbETH': {
                'protocol': 'coinbase',
                'underlying': 'ETH',
                'type': 'centralized_staking',
                'apy_estimate': 3.8
            },
            'sfrxETH': {
                'protocol': 'frax',
                'underlying': 'ETH',
                'type': 'algorithmic_staking',
                'apy_estimate': 5.2
            }
        }
        
        self.session_timeout = aiohttp.ClientTimeout(total=30)  # Reduced timeout
        self.max_retries = 2  # Reduced retries for faster failure
        self.retry_delay = 2
    
    async def get_staking_metrics(self, address: str) -> Dict[str, Any]:
        """Get comprehensive staking metrics and behavior analysis"""
        
        logger.info(f"Fetching enhanced staking metrics for address: {address}")
        
        if not self.api_key:
            logger.warning("Moralis API key not configured, using enhanced fallback analysis")
            return self._get_enhanced_fallback_data(address)
        
        try:
            # Enhanced data collection with better timeout handling
            staking_data = await self._collect_comprehensive_staking_data(address)
            
            # Process and analyze data with safe method calls
            staking_metrics = self._calculate_enhanced_staking_metrics(staking_data, address)
            
            logger.info(f"Successfully processed enhanced staking data for {address}")
            return staking_metrics
            
        except Exception as e:
            logger.error(f"Error fetching Moralis staking data: {str(e)}")
            return self._get_enhanced_fallback_data(address)
    
    async def _collect_comprehensive_staking_data(self, address: str) -> Dict[str, Any]:
        """Collect comprehensive staking data from multiple endpoints with timeout protection"""
        
        try:
            # Use shorter timeout and better error handling
            connector = aiohttp.TCPConnector(
                limit=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30
            )
            
            async with aiohttp.ClientSession(
                headers=self.headers,
                timeout=self.session_timeout,
                connector=connector
            ) as session:
                
                # Parallel data collection with individual timeouts
                collection_tasks = [
                    asyncio.wait_for(
                        self._get_wallet_tokens_with_retry(session, address),
                        timeout=8
                    ),
                    asyncio.wait_for(
                        self._get_defi_positions_with_retry(session, address),
                        timeout=8
                    ),
                    asyncio.wait_for(
                        self._get_wallet_history_with_retry(session, address),
                        timeout=12
                    ),
                    asyncio.wait_for(
                        self._get_nft_transfers_with_retry(session, address),
                        timeout=5
                    )
                ]
                
                # Execute with timeout protection
                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*collection_tasks, return_exceptions=True),
                        timeout=25  # Total timeout of 25 seconds
                    )
                    
                    return {
                        'wallet_tokens': results[0] if not isinstance(results[0], Exception) else {'success': False, 'data': [], 'error': str(results[0])},
                        'defi_positions': results[1] if not isinstance(results[1], Exception) else {'success': False, 'data': [], 'error': str(results[1])},
                        'wallet_history': results[2] if not isinstance(results[2], Exception) else {'success': False, 'data': [], 'error': str(results[2])},
                        'nft_transfers': results[3] if not isinstance(results[3], Exception) else {'success': False, 'data': [], 'error': str(results[3])}
                    }
                    
                except asyncio.TimeoutError:
                    logger.warning("Moralis data collection timed out")
                    return {
                        'wallet_tokens': {'success': False, 'data': [], 'error': 'timeout'},
                        'defi_positions': {'success': False, 'data': [], 'error': 'timeout'},
                        'wallet_history': {'success': False, 'data': [], 'error': 'timeout'},
                        'nft_transfers': {'success': False, 'data': [], 'error': 'timeout'}
                    }
                    
        except Exception as e:
            logger.error(f"Session creation failed: {str(e)}")
            return {
                'wallet_tokens': {'success': False, 'data': [], 'error': str(e)},
                'defi_positions': {'success': False, 'data': [], 'error': str(e)},
                'wallet_history': {'success': False, 'data': [], 'error': str(e)},
                'nft_transfers': {'success': False, 'data': [], 'error': str(e)}
            }
    
    async def _get_wallet_tokens_with_retry(self, session: aiohttp.ClientSession, address: str) -> Dict:
        """Get wallet tokens with retry logic and error handling"""
        
        for attempt in range(self.max_retries):
            try:
                url = f'{self.base_url}/wallets/{address}/tokens'
                params = {'chain': 'eth', 'limit': 100}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data.get('result', []),
                            'error': None
                        }
                    else:
                        if attempt == self.max_retries - 1:
                            error_text = await response.text() if response.status != 429 else "Rate limited"
                            return {
                                'success': False,
                                'data': [],
                                'error': f"HTTP {response.status}: {error_text}"
                            }
                        
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'data': [],
                        'error': str(e)
                    }
                await asyncio.sleep(self.retry_delay * (attempt + 1))
    
    async def _get_defi_positions_with_retry(self, session: aiohttp.ClientSession, address: str) -> Dict:
        """Get DeFi positions with retry logic and error handling"""
        
        for attempt in range(self.max_retries):
            try:
                url = f'{self.base_url}/wallets/{address}/defi/positions'
                params = {'chain': 'eth'}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data.get('result', []),
                            'error': None
                        }
                    else:
                        if attempt == self.max_retries - 1:
                            return {
                                'success': False,
                                'data': [],
                                'error': f"HTTP {response.status}"
                            }
                        
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'data': [],
                        'error': str(e)
                    }
                await asyncio.sleep(self.retry_delay * (attempt + 1))
    
    async def _get_wallet_history_with_retry(self, session: aiohttp.ClientSession, address: str) -> Dict:
        """Get wallet transaction history with retry logic and error handling"""
        
        for attempt in range(self.max_retries):
            try:
                url = f'{self.base_url}/wallets/{address}/history'
                params = {'chain': 'eth', 'limit': 50, 'order': 'DESC'}  # Reduced limit for faster response
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data.get('result', []),
                            'error': None
                        }
                    else:
                        if attempt == self.max_retries - 1:
                            return {
                                'success': False,
                                'data': [],
                                'error': f"HTTP {response.status}"
                            }
                        
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'data': [],
                        'error': str(e)
                    }
                await asyncio.sleep(self.retry_delay * (attempt + 1))
    
    async def _get_nft_transfers_with_retry(self, session: aiohttp.ClientSession, address: str) -> Dict:
        """Get NFT transfers for additional context with error handling"""
        
        try:
            url = f'{self.base_url}/wallets/{address}/nfts/transfers'
            params = {'chain': 'eth', 'limit': 25}  # Reduced limit
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'data': data.get('result', []),
                        'error': None
                    }
                else:
                    return {'success': False, 'data': [], 'error': f"HTTP {response.status}"}
                    
        except Exception as e:
            return {'success': False, 'data': [], 'error': str(e)}
    
    def _calculate_enhanced_staking_metrics(self, staking_data: Dict, address: str) -> Dict[str, Any]:
        """
        FIXED: Calculate comprehensive staking metrics with enhanced analytics
        """
        
        # Extract data from collection results with safe access
        wallet_tokens = staking_data.get('wallet_tokens', {}).get('data', [])
        defi_positions = staking_data.get('defi_positions', {}).get('data', [])
        wallet_history = staking_data.get('wallet_history', {}).get('data', [])
        
        # Enhanced staking analysis with error handling
        try:
            staking_token_analysis = self._analyze_staking_tokens(wallet_tokens)
            defi_staking_analysis = self._analyze_defi_staking_positions(defi_positions)
            staking_history_analysis = self._analyze_staking_history(wallet_history)
            
            # Platform and protocol analysis
            platform_analysis = self._analyze_staking_platforms(staking_token_analysis, defi_staking_analysis)
            
            # Risk and diversification analysis
            risk_analysis = self._analyze_staking_risk_profile(staking_token_analysis, platform_analysis)
            
            # Behavioral pattern analysis - FIXED METHOD CALL
            behavior_analysis = self._analyze_staking_behavior_patterns(staking_history_analysis, staking_token_analysis)
            
            # Calculate derived metrics with safe access
            loyalty_score = self._calculate_staking_loyalty_score(behavior_analysis, platform_analysis)
            diversification_score = self._calculate_platform_diversification_score(platform_analysis)
            sophistication_score = self._calculate_staking_sophistication(platform_analysis, behavior_analysis)
            
            return {
                # Core metrics
                'total_staked_usd': staking_token_analysis['total_staked_value'] + defi_staking_analysis['total_defi_staking_value'],
                'platform_count': platform_analysis['unique_platforms'],
                'avg_duration_days': behavior_analysis['estimated_avg_duration_days'],
                'platform_diversity': diversification_score,
                'claim_frequency': behavior_analysis['reward_claim_frequency'],
                'staking_loyalty_score': loyalty_score,
                'sophistication_score': sophistication_score,
                
                # Enhanced analytics
                'staking_token_analysis': staking_token_analysis,
                'defi_staking_analysis': defi_staking_analysis,
                'platform_analysis': platform_analysis,
                'risk_analysis': risk_analysis,
                'behavior_analysis': behavior_analysis,
                
                # Additional insights
                'staking_experience_level': self._determine_staking_experience_level(loyalty_score, sophistication_score, platform_analysis),
                'estimated_annual_rewards_usd': self._estimate_annual_staking_rewards(staking_token_analysis),
                'data_quality_score': self._calculate_staking_data_quality(staking_data),
                'collection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in staking metrics calculation: {str(e)}")
            return self._get_enhanced_fallback_data(address)
    
    def _analyze_staking_tokens(self, wallet_tokens: List[Dict]) -> Dict[str, Any]:
        """Analyze staking tokens in the wallet with error handling"""
        
        staking_positions = []
        total_staked_value = 0
        staking_protocols = set()
        token_breakdown = {}
        
        try:
            for token in wallet_tokens:
                symbol = token.get('symbol', '').upper()
                balance = float(token.get('balance_formatted', 0) or 0)
                usd_value = float(token.get('usd_value', 0) or 0)
                
                # Check if it's a known staking token
                if symbol in self.staking_tokens and balance > 0:
                    token_info = self.staking_tokens[symbol]
                    
                    staking_positions.append({
                        'symbol': symbol,
                        'balance': balance,
                        'usd_value': usd_value,
                        'protocol': token_info['protocol'],
                        'type': token_info['type'],
                        'estimated_apy': token_info['apy_estimate']
                    })
                    
                    total_staked_value += usd_value
                    staking_protocols.add(token_info['protocol'])
                    token_breakdown[symbol] = {
                        'balance': balance,
                        'usd_value': usd_value,
                        'protocol': token_info['protocol']
                    }
        except Exception as e:
            logger.warning(f"Error analyzing staking tokens: {str(e)}")
        
        return {
            'staking_positions': staking_positions,
            'total_staked_value': total_staked_value,
            'staking_protocols': list(staking_protocols),
            'unique_staking_tokens': len(staking_positions),
            'token_breakdown': token_breakdown,
            'largest_position': max(staking_positions, key=lambda x: x['usd_value']) if staking_positions else None
        }
    
    def _analyze_defi_staking_positions(self, defi_positions: List[Dict]) -> Dict[str, Any]:
        """Analyze DeFi staking positions with error handling"""
        
        defi_staking_positions = []
        total_defi_staking_value = 0
        defi_staking_protocols = set()
        
        staking_keywords = ['staking', 'stake', 'validator', 'delegate', 'bond', 'lock']
        
        try:
            for position in defi_positions:
                protocol_name = position.get('protocol_name', '').lower()
                protocol_id = position.get('protocol_id', '').lower()
                position_value = float(position.get('position_value_usd', 0) or 0)
                position_type = position.get('position_type', '').lower()
                
                # Check if it's a staking-related position
                is_staking_position = (
                    any(keyword in protocol_name for keyword in staking_keywords) or
                    any(keyword in protocol_id for keyword in staking_keywords) or
                    any(keyword in position_type for keyword in staking_keywords)
                )
                
                if is_staking_position and position_value > 0:
                    defi_staking_positions.append({
                        'protocol_name': protocol_name,
                        'protocol_id': protocol_id,
                        'position_value_usd': position_value,
                        'position_type': position_type
                    })
                    
                    total_defi_staking_value += position_value
                    defi_staking_protocols.add(protocol_name)
        except Exception as e:
            logger.warning(f"Error analyzing DeFi staking positions: {str(e)}")
        
        return {
            'defi_staking_positions': defi_staking_positions,
            'total_defi_staking_value': total_defi_staking_value,
            'defi_staking_protocols': list(defi_staking_protocols),
            'unique_defi_staking_protocols': len(defi_staking_protocols)
        }
    
    def _analyze_staking_history(self, wallet_history: List[Dict]) -> Dict[str, Any]:
        """Analyze staking-related transaction history with error handling"""
        
        staking_transactions = []
        stake_events = []
        unstake_events = []
        claim_events = []
        
        staking_keywords = ['stake', 'unstake', 'claim', 'delegate', 'withdraw', 'deposit']
        
        try:
            for tx in wallet_history:
                summary = tx.get('summary', '').lower()
                category = tx.get('category', '').lower()
                
                # Check if transaction is staking-related
                is_staking_tx = any(keyword in summary for keyword in staking_keywords)
                
                if is_staking_tx:
                    tx_data = {
                        'hash': tx.get('hash'),
                        'block_timestamp': tx.get('block_timestamp'),
                        'summary': summary,
                        'category': category,
                        'value': tx.get('value', 0)
                    }
                    
                    staking_transactions.append(tx_data)
                    
                    # Categorize transaction type
                    if 'stake' in summary and 'unstake' not in summary:
                        stake_events.append(tx_data)
                    elif 'unstake' in summary or 'withdraw' in summary:
                        unstake_events.append(tx_data)
                    elif 'claim' in summary:
                        claim_events.append(tx_data)
        except Exception as e:
            logger.warning(f"Error analyzing staking history: {str(e)}")
        
        # Calculate frequency and patterns
        reward_claim_frequency = len(claim_events)
        stake_to_unstake_ratio = len(stake_events) / max(1, len(unstake_events))
        
        # Estimate duration based on transaction patterns
        estimated_duration = self._estimate_staking_duration(stake_events, unstake_events)
        
        return {
            'total_staking_transactions': len(staking_transactions),
            'stake_events': len(stake_events),
            'unstake_events': len(unstake_events),
            'claim_events': len(claim_events),
            'reward_claim_frequency': reward_claim_frequency,
            'stake_to_unstake_ratio': stake_to_unstake_ratio,
            'estimated_avg_duration_days': estimated_duration,
            'recent_staking_activity': self._analyze_recent_staking_activity(staking_transactions)
        }
    
    def _analyze_staking_platforms(self, staking_tokens: Dict, defi_staking: Dict) -> Dict[str, Any]:
        """Analyze staking platform distribution and preferences with error handling"""
        
        all_platforms = set()
        platform_values = {}
        platform_types = {}
        
        try:
            # Add platforms from staking tokens
            for protocol in staking_tokens.get('staking_protocols', []):
                all_platforms.add(protocol)
                
                # Calculate platform value
                protocol_value = sum([
                    pos['usd_value'] for pos in staking_tokens.get('staking_positions', [])
                    if pos['protocol'] == protocol
                ])
                platform_values[protocol] = platform_values.get(protocol, 0) + protocol_value
                
                # Set platform type
                if protocol in self.staking_protocols:
                    platform_types[protocol] = self.staking_protocols[protocol]['category']
            
            # Add platforms from DeFi staking
            for protocol in defi_staking.get('defi_staking_protocols', []):
                all_platforms.add(protocol)
                
                protocol_value = sum([
                    pos['position_value_usd'] for pos in defi_staking.get('defi_staking_positions', [])
                    if pos['protocol_name'] == protocol
                ])
                platform_values[protocol] = platform_values.get(protocol, 0) + protocol_value
            
            # Platform preference analysis
            dominant_platform = max(platform_values.items(), key=lambda x: x[1])[0] if platform_values else None
            platform_concentration = max(platform_values.values()) / sum(platform_values.values()) if platform_values else 0
            
        except Exception as e:
            logger.warning(f"Error analyzing staking platforms: {str(e)}")
            dominant_platform = None
            platform_concentration = 0
        
        return {
            'all_platforms': list(all_platforms),
            'unique_platforms': len(all_platforms),
            'platform_values': platform_values,
            'platform_types': platform_types,
            'dominant_platform': dominant_platform,
            'platform_concentration_ratio': platform_concentration,
            'diversification_level': 'high' if len(all_platforms) > 3 else 'medium' if len(all_platforms) > 1 else 'low'
        }
    
    def _analyze_staking_risk_profile(self, staking_tokens: Dict, platform_analysis: Dict) -> Dict[str, Any]:
        """Analyze staking risk profile with error handling"""
        
        risk_distribution = {'low': 0, 'medium': 0, 'high': 0}
        total_value = staking_tokens.get('total_staked_value', 0)
        
        try:
            # Assess risk based on protocols
            for position in staking_tokens.get('staking_positions', []):
                protocol = position.get('protocol', '')
                value = position.get('usd_value', 0)
                
                if protocol in self.staking_protocols:
                    risk_level = self.staking_protocols[protocol]['risk_level']
                    risk_distribution[risk_level] += value
            
            # Calculate risk percentages
            risk_percentages = {}
            if total_value > 0:
                for risk_level, value in risk_distribution.items():
                    risk_percentages[risk_level] = (value / total_value) * 100
            
            # Overall risk assessment
            overall_risk_score = (
                risk_percentages.get('low', 0) * 0.2 + 
                risk_percentages.get('medium', 0) * 0.5 + 
                risk_percentages.get('high', 0) * 0.8
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing risk profile: {str(e)}")
            risk_percentages = {'low': 0, 'medium': 0, 'high': 0}
            overall_risk_score = 0
        
        return {
            'risk_distribution_usd': risk_distribution,
            'risk_distribution_percentage': risk_percentages,
            'overall_risk_score': overall_risk_score,
            'risk_level': 'high' if overall_risk_score > 60 else 'medium' if overall_risk_score > 30 else 'low',
            'concentration_risk': platform_analysis.get('platform_concentration_ratio', 0)
        }
    
    def _analyze_staking_behavior_patterns(self, history_analysis: Dict, token_analysis: Dict) -> Dict[str, Any]:
        """
        FIXED: Analyze behavioral patterns in staking activities
        """
        
        # Activity consistency - SAFELY get values with defaults
        claim_frequency = history_analysis.get('reward_claim_frequency', 0)
        stake_unstake_ratio = history_analysis.get('stake_to_unstake_ratio', 1.0)
        estimated_duration = history_analysis.get('estimated_avg_duration_days', 0)
        
        # Position holding patterns
        position_stability = 'stable' if stake_unstake_ratio > 2 else 'active' if stake_unstake_ratio > 0.5 else 'volatile'
        
        # Reward optimization behavior
        reward_optimization_score = min(100, claim_frequency * 10)
        
        return {
            'position_stability': position_stability,
            'reward_claim_pattern': 'frequent' if claim_frequency > 10 else 'moderate' if claim_frequency > 3 else 'infrequent',
            'reward_optimization_score': reward_optimization_score,
            'stake_unstake_behavior': 'holder' if stake_unstake_ratio > 3 else 'balanced' if stake_unstake_ratio > 0.8 else 'trader',
            'estimated_avg_duration_days': estimated_duration,
            'reward_claim_frequency': claim_frequency  # ENSURE THIS KEY IS ALWAYS PRESENT
        }
    
    def _analyze_recent_staking_activity(self, staking_transactions: List) -> Dict[str, Any]:
        """Analyze recent staking activity patterns with error handling"""
        
        if not staking_transactions:
            return {
                'recent_transactions_count': 0,
                'is_recently_active': False,
                'activity_level': 'none'
            }
        
        try:
            # Count recent transactions (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_count = 0
            
            for tx in staking_transactions:
                tx_timestamp = tx.get('block_timestamp')
                if tx_timestamp:
                    try:
                        tx_date = datetime.fromisoformat(tx_timestamp.replace('Z', '+00:00'))
                        if tx_date > thirty_days_ago:
                            recent_count += 1
                    except Exception:
                        continue
            
            return {
                'recent_transactions_count': recent_count,
                'is_recently_active': recent_count > 0,
                'activity_level': 'high' if recent_count > 5 else 'medium' if recent_count > 1 else 'low'
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing recent activity: {str(e)}")
            return {
                'recent_transactions_count': 0,
                'is_recently_active': False,
                'activity_level': 'none'
            }
    
    def _estimate_staking_duration(self, stake_events: List, unstake_events: List) -> float:
        """Estimate average staking duration based on transaction patterns"""
        
        if not stake_events:
            return 0.0
        
        try:
            if stake_events and unstake_events:
                # If there are both stake and unstake events, estimate based on frequency
                stake_frequency = len(stake_events)
                unstake_frequency = len(unstake_events)
                
                # Rough estimation: if someone stakes frequently and rarely unstakes, they hold longer
                estimated_days = min(365, (stake_frequency / max(1, unstake_frequency)) * 30)
                return estimated_days
            elif stake_events and not unstake_events:
                # Only staking events, assume long-term holding
                return 180
            else:
                # No clear pattern
                return 30
        except Exception:
            return 0.0
    
    def _calculate_staking_loyalty_score(self, behavior_analysis: Dict, platform_analysis: Dict) -> float:
        """Calculate overall staking loyalty score with safe access"""
        
        try:
            # Duration component (40% weight) - SAFE ACCESS
            duration_days = behavior_analysis.get('estimated_avg_duration_days', 0)
            duration_score = min(40, (duration_days / 365) * 40)
            
            # Stability component (30% weight) - SAFE ACCESS
            position_stability = behavior_analysis.get('position_stability', 'unknown')
            stability_score = 30 if position_stability == 'stable' else 20 if position_stability == 'active' else 10
            
            # Platform loyalty component (30% weight) - SAFE ACCESS
            concentration = platform_analysis.get('platform_concentration_ratio', 0)
            platform_loyalty_score = concentration * 30
            
            total_score = duration_score + stability_score + platform_loyalty_score
            return min(100, total_score)
            
        except Exception as e:
            logger.warning(f"Error calculating loyalty score: {str(e)}")
            return 0.0
    
    def _calculate_platform_diversification_score(self, platform_analysis: Dict) -> float:
        """Calculate platform diversification score with error handling"""
        
        try:
            unique_platforms = platform_analysis.get('unique_platforms', 0)
            concentration_ratio = platform_analysis.get('platform_concentration_ratio', 1)
            
            # Base diversification score
            base_score = min(60, unique_platforms * 15)
            
            # Concentration penalty (less concentration = better diversification)
            concentration_bonus = (1 - concentration_ratio) * 40
            
            return min(100, base_score + concentration_bonus)
            
        except Exception as e:
            logger.warning(f"Error calculating diversification score: {str(e)}")
            return 0.0
    
    def _calculate_staking_sophistication(self, platform_analysis: Dict, behavior_analysis: Dict) -> int:
        """Calculate staking sophistication score with error handling"""
        
        try:
            sophistication = 0
            
            # Platform sophistication
            unique_platforms = platform_analysis.get('unique_platforms', 0)
            if unique_platforms > 3:
                sophistication += 30
            elif unique_platforms > 1:
                sophistication += 20
            elif unique_platforms == 1:
                sophistication += 10
            
            # Behavior sophistication
            reward_optimization = behavior_analysis.get('reward_optimization_score', 0)
            sophistication += min(25, reward_optimization / 4)
            
            # Platform diversity sophistication
            diversification_level = platform_analysis.get('diversification_level', 'low')
            if diversification_level == 'high':
                sophistication += 25
            elif diversification_level == 'medium':
                sophistication += 15
            else:
                sophistication += 5
            
            # Stability sophistication
            position_stability = behavior_analysis.get('position_stability', 'unknown')
            if position_stability == 'stable':
                sophistication += 20
            elif position_stability == 'active':
                sophistication += 10
            
            return min(100, sophistication)
            
        except Exception as e:
            logger.warning(f"Error calculating sophistication score: {str(e)}")
            return 0
    
    def _determine_staking_experience_level(self, loyalty_score: float, sophistication_score: int, platform_analysis: Dict) -> str:
        """Determine staking experience level with error handling"""
        
        try:
            platforms = platform_analysis.get('unique_platforms', 0)
            total_value = sum(platform_analysis.get('platform_values', {}).values())
            
            if loyalty_score > 80 and sophistication_score > 80 and platforms > 3 and total_value > 50000:
                return 'expert'
            elif loyalty_score > 60 and sophistication_score > 60 and platforms > 2 and total_value > 10000:
                return 'advanced'
            elif loyalty_score > 40 and sophistication_score > 40 and platforms > 1 and total_value > 1000:
                return 'intermediate'
            elif platforms > 0 and total_value > 0:
                return 'beginner'
            else:
                return 'newcomer'
                
        except Exception as e:
            logger.warning(f"Error determining experience level: {str(e)}")
            return 'newcomer'
    
    def _estimate_annual_staking_rewards(self, staking_token_analysis: Dict) -> float:
        """Estimate annual staking rewards in USD with error handling"""
        
        try:
            total_estimated_rewards = 0
            
            for position in staking_token_analysis.get('staking_positions', []):
                position_value = position.get('usd_value', 0)
                estimated_apy = position.get('estimated_apy', 0) / 100  # Convert percentage to decimal
                
                annual_reward = position_value * estimated_apy
                total_estimated_rewards += annual_reward
            
            return round(total_estimated_rewards, 2)
            
        except Exception as e:
            logger.warning(f"Error estimating rewards: {str(e)}")
            return 0.0
    
    def _calculate_staking_data_quality(self, staking_data: Dict) -> int:
        """Calculate staking data quality score with error handling"""
        
        try:
            quality_score = 0
            
            # Wallet tokens data quality (max 40 points)
            wallet_tokens_result = staking_data.get('wallet_tokens', {})
            if wallet_tokens_result.get('success'):
                token_count = len(wallet_tokens_result.get('data', []))
                quality_score += min(40, token_count * 2)
            
            # DeFi positions data quality (max 30 points)
            defi_result = staking_data.get('defi_positions', {})
            if defi_result.get('success'):
                quality_score += 30
            
            # Transaction history quality (max 30 points)
            history_result = staking_data.get('wallet_history', {})
            if history_result.get('success'):
                tx_count = len(history_result.get('data', []))
                quality_score += min(30, tx_count // 2)  # 1 point per 2 transactions
            
            return min(100, quality_score)
            
        except Exception as e:
            logger.warning(f"Error calculating data quality: {str(e)}")
            return 0
    
    def _get_enhanced_fallback_data(self, address: str) -> Dict[str, Any]:
        """Enhanced fallback data when API is not available"""
        
        logger.info("Using enhanced fallback staking data")
        
        return {
            'total_staked_usd': 0.0,
            'platform_count': 0,
            'avg_duration_days': 0.0,
            'platform_diversity': 0.0,
            'claim_frequency': 0,
            'staking_loyalty_score': 0.0,
            'sophistication_score': 0,
            'staking_token_analysis': {
                'staking_positions': [],
                'total_staked_value': 0,
                'staking_protocols': [],
                'unique_staking_tokens': 0
            },
            'defi_staking_analysis': {
                'defi_staking_positions': [],
                'total_defi_staking_value': 0,
                'defi_staking_protocols': [],
                'unique_defi_staking_protocols': 0
            },
            'platform_analysis': {
                'all_platforms': [],
                'unique_platforms': 0,
                'platform_values': {},
                'diversification_level': 'none'
            },
            'risk_analysis': {
                'risk_score': 0,
                'risk_level': 'unknown'
            },
            'behavior_analysis': {
                'position_stability': 'unknown',
                'reward_claim_pattern': 'unknown',
                'estimated_avg_duration_days': 0,
                'reward_claim_frequency': 0  # KEY FIX: Always present
            },
            'staking_experience_level': 'newcomer',
            'estimated_annual_rewards_usd': 0.0,
            'data_quality_score': 0,
            'collection_timestamp': datetime.now().isoformat()
        }


# Test implementation
async def test_enhanced_moralis_client():
    """Comprehensive test for fixed Moralis client"""
    
    client = MoralisClient()
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik's address
    
    try:
        print("🧪 Testing Fixed Moralis Client...")
        print("=" * 50)
        
        metrics = await client.get_staking_metrics(test_address)
        
        print(f"✅ Address: {test_address}")
        print(f"✅ Total Staked: ${metrics['total_staked_usd']:,.2f}")
        print(f"✅ Platform Count: {metrics['platform_count']}")
        print(f"✅ Avg Duration: {metrics['avg_duration_days']:.1f} days")
        print(f"✅ Loyalty Score: {metrics['staking_loyalty_score']:.1f}/100")
        print(f"✅ Sophistication Score: {metrics['sophistication_score']}/100")
        print(f"✅ Experience Level: {metrics['staking_experience_level']}")
        print(f"✅ Data Quality: {metrics['data_quality_score']}/100")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Moralis client: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_moralis_client())
