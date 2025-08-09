# clients/zapper_client.py
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import os
import json
from loguru import logger
from datetime import datetime

class ZapperClient:
    """
    Enhanced Zapper API client for comprehensive DeFi portfolio analysis
    Handles: Multi-chain DeFi positions, protocol interactions, LP tokens, yield farming
    """
    
    def __init__(self):
        self.api_key = os.getenv('ZAPPER_API_KEY')
        if not self.api_key:
            raise ValueError("ZAPPER_API_KEY not found in environment variables")
        
        self.base_url = 'https://api.zapper.fi/v2'
        self.headers = {
            'Authorization': f'Basic {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Enhanced network support
        self.supported_networks = [
            'ethereum',
            'polygon', 
            'arbitrum',
            'optimism',
            'base',
            'binance-smart-chain',
            'avalanche'
        ]
        
        self.session_timeout = aiohttp.ClientTimeout(total=45)
        self.max_retries = 3
        self.retry_delay = 2
    
    async def get_defi_metrics(self, address: str) -> Dict[str, Any]:
        """
        Get comprehensive DeFi metrics with enhanced analytics
        """
        logger.info(f"Fetching enhanced DeFi metrics for address: {address}")
        
        try:
            if not self._is_valid_address(address):
                raise ValueError(f"Invalid address format: {address}")
            
            # Enhanced data collection with retry logic
            data_results = await self._collect_all_defi_data_with_retry(address)
            
            # Process and analyze collected data
            defi_metrics = self._calculate_enhanced_defi_metrics(data_results, address)
            
            logger.info(f"Successfully processed enhanced DeFi data for {address}")
            return defi_metrics
            
        except Exception as e:
            logger.error(f"Error fetching DeFi metrics for {address}: {str(e)}")
            return self._get_empty_defi_metrics()
    
    async def _collect_all_defi_data_with_retry(self, address: str) -> Dict[str, Any]:
        """Enhanced data collection with comprehensive retry logic"""
        
        async with aiohttp.ClientSession(
            headers=self.headers,
            timeout=self.session_timeout
        ) as session:
            
            # Parallel data collection with retry
            collection_tasks = [
                self._get_data_with_retry(session, 'balances', address),
                self._get_data_with_retry(session, 'apps', address),
                self._get_data_with_retry(session, 'nft_balances', address),
                self._get_data_with_retry(session, 'tokens', address)
            ]
            
            results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            return {
                'balances': results[0] if not isinstance(results[0], Exception) else {'success': False, 'data': [], 'error': str(results[0])},
                'apps': results[1] if not isinstance(results[1], Exception) else {'success': False, 'data': {}, 'error': str(results[1])},
                'nft_balances': results[2] if not isinstance(results[2], Exception) else {'success': False, 'data': [], 'error': str(results[2])},
                'tokens': results[3] if not isinstance(results[3], Exception) else {'success': False, 'data': [], 'error': str(results[3])}
            }
    
    async def _get_data_with_retry(self, session: aiohttp.ClientSession, 
                                 endpoint: str, address: str) -> Dict[str, Any]:
        """Get data from specific endpoint with retry logic"""
        
        endpoint_configs = {
            'balances': {
                'url': f'{self.base_url}/balances',
                'params': {
                    'addresses[]': address,
                    'networks[]': self.supported_networks
                }
            },
            'apps': {
                'url': f'{self.base_url}/apps',
                'params': {
                    'addresses[]': address,
                    'networks[]': self.supported_networks[:4]  # Limit for rate limits
                }
            },
            'nft_balances': {
                'url': f'{self.base_url}/nft/balances',
                'params': {
                    'addresses[]': address,
                    'networks[]': ['ethereum', 'polygon', 'arbitrum']
                }
            },
            'tokens': {
                'url': f'{self.base_url}/tokens/balances',
                'params': {
                    'addresses[]': address,
                    'networks[]': ['ethereum', 'polygon']
                }
            }
        }
        
        config = endpoint_configs.get(endpoint)
        if not config:
            return {'success': False, 'data': [], 'error': 'Unknown endpoint'}
        
        for attempt in range(self.max_retries):
            try:
                async with session.get(config['url'], params=config['params']) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data.get(address.lower(), [] if endpoint != 'apps' else {}),
                            'error': None,
                            'attempt': attempt + 1
                        }
                    else:
                        error_text = await response.text()
                        if attempt == self.max_retries - 1:
                            return {
                                'success': False,
                                'data': [] if endpoint != 'apps' else {},
                                'error': f"HTTP {response.status}: {error_text}",
                                'attempts_made': self.max_retries
                            }
                        
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'data': [] if endpoint != 'apps' else {},
                        'error': str(e),
                        'attempts_made': self.max_retries
                    }
                
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
    
    def _calculate_enhanced_defi_metrics(self, data_results: Dict, address: str) -> Dict[str, Any]:
        """Calculate comprehensive DeFi engagement metrics with advanced analytics"""
        
        # Extract data from results
        balances_data = data_results.get('balances', {}).get('data', [])
        apps_data = data_results.get('apps', {}).get('data', {})
        nft_data = data_results.get('nft_balances', {}).get('data', [])
        tokens_data = data_results.get('tokens', {}).get('data', [])
        
        # Enhanced protocol analysis
        protocol_analysis = self._analyze_protocols_enhanced(balances_data, apps_data)
        
        # Liquidity provision analysis
        liquidity_analysis = self._analyze_liquidity_provision(balances_data, apps_data)
        
        # Yield farming analysis
        yield_analysis = self._analyze_yield_farming_enhanced(balances_data, apps_data)
        
        # Risk assessment
        risk_analysis = self._analyze_defi_risk_profile(balances_data, apps_data)
        
        # Portfolio composition analysis
        portfolio_analysis = self._analyze_portfolio_composition(balances_data, tokens_data)
        
        # Network distribution analysis
        network_analysis = self._analyze_network_distribution(balances_data)
        
        # Calculate derived metrics
        diversity_score = self._calculate_enhanced_diversity_score(protocol_analysis)
        interaction_depth = self._calculate_interaction_depth_score(protocol_analysis, apps_data)
        sophistication_score = self._calculate_defi_sophistication(protocol_analysis, yield_analysis, liquidity_analysis)
        
        return {
            # Core metrics
            'unique_protocols': protocol_analysis['unique_protocols_count'],
            'total_balance_usd': portfolio_analysis['total_portfolio_value'],
            'lp_positions': liquidity_analysis['total_lp_positions'],
            'diversity_score': diversity_score,
            'interaction_depth': interaction_depth,
            'sophistication_score': sophistication_score,
            
            # Enhanced analytics
            'protocol_analysis': protocol_analysis,
            'liquidity_analysis': liquidity_analysis,
            'yield_analysis': yield_analysis,
            'risk_analysis': risk_analysis,
            'portfolio_analysis': portfolio_analysis,
            'network_analysis': network_analysis,
            
            # Additional metrics
            'nft_holdings': len(nft_data),
            'defi_experience_level': self._determine_experience_level(protocol_analysis, portfolio_analysis, sophistication_score),
            'data_quality_score': self._calculate_enhanced_data_quality(data_results),
            'collection_timestamp': datetime.now().isoformat()
        }
    
    def _analyze_protocols_enhanced(self, balances_data: List, apps_data: Dict) -> Dict[str, Any]:
        """Enhanced protocol analysis with categorization and scoring"""
        
        unique_protocols = set()
        protocol_categories = {
            'dex': {'protocols': set(), 'value': 0},
            'lending': {'protocols': set(), 'value': 0},
            'staking': {'protocols': set(), 'value': 0},
            'yield_farming': {'protocols': set(), 'value': 0},
            'derivatives': {'protocols': set(), 'value': 0},
            'insurance': {'protocols': set(), 'value': 0},
            'bridge': {'protocols': set(), 'value': 0},
            'dao': {'protocols': set(), 'value': 0}
        }
        
        protocol_details = {}
        total_protocol_value = 0
        
        # Analyze balance data
        for balance_item in balances_data:
            app_id = balance_item.get('appId', '').lower()
            balance_usd = balance_item.get('balanceUSD', 0)
            
            if app_id and balance_usd > 0:
                unique_protocols.add(app_id)
                total_protocol_value += balance_usd
                
                # Categorize protocol
                category = self._categorize_protocol_enhanced(app_id)
                if category in protocol_categories:
                    protocol_categories[category]['protocols'].add(app_id)
                    protocol_categories[category]['value'] += balance_usd
                
                # Store protocol details
                protocol_details[app_id] = {
                    'balance_usd': balance_usd,
                    'category': category,
                    'network': balance_item.get('network', 'unknown'),
                    'tokens': self._extract_protocol_tokens(balance_item)
                }
        
        # Analyze apps data
        for network, network_data in apps_data.items():
            if isinstance(network_data, list):
                for app_entry in network_data:
                    app_id = app_entry.get('appId', '').lower()
                    if app_id:
                        unique_protocols.add(app_id)
                        if app_id not in protocol_details:
                            protocol_details[app_id] = {
                                'balance_usd': app_entry.get('balanceUSD', 0),
                                'category': self._categorize_protocol_enhanced(app_id),
                                'network': network,
                                'products': app_entry.get('products', [])
                            }
        
        return {
            'unique_protocols_count': len(unique_protocols),
            'unique_protocols_list': list(unique_protocols),
            'protocol_categories': {k: {'count': len(v['protocols']), 'value_usd': v['value'], 'protocols': list(v['protocols'])} 
                                  for k, v in protocol_categories.items()},
            'protocol_details': protocol_details,
            'total_protocol_value': total_protocol_value,
            'category_diversity': len([cat for cat, data in protocol_categories.items() if len(data['protocols']) > 0])
        }
    
    def _categorize_protocol_enhanced(self, app_id: str) -> str:
        """Enhanced protocol categorization with more categories"""
        
        app_id_lower = app_id.lower()
        
        # DEX protocols
        if any(keyword in app_id_lower for keyword in ['uniswap', 'sushiswap', 'curve', 'balancer', '1inch', 'pancake', '0x', 'kyber']):
            return 'dex'
        
        # Lending protocols
        elif any(keyword in app_id_lower for keyword in ['compound', 'aave', 'maker', 'benqi', 'cream', 'radiant', 'euler']):
            return 'lending'
        
        # Staking protocols
        elif any(keyword in app_id_lower for keyword in ['lido', 'rocket', 'stakewise', 'staking', 'frax', 'ankr']):
            return 'staking'
        
        # Yield farming
        elif any(keyword in app_id_lower for keyword in ['yearn', 'harvest', 'pickle', 'farm', 'convex', 'beefy']):
            return 'yield_farming'
        
        # Derivatives
        elif any(keyword in app_id_lower for keyword in ['synthetix', 'hegic', 'opyn', 'dydx', 'gmx', 'perpetual']):
            return 'derivatives'
        
        # Bridge protocols
        elif any(keyword in app_id_lower for keyword in ['bridge', 'hop', 'cbridge', 'multichain', 'wormhole']):
            return 'bridge'
        
        # Insurance
        elif any(keyword in app_id_lower for keyword in ['nexus', 'cover', 'insurance', 'unslashed']):
            return 'insurance'
        
        # DAO protocols
        elif any(keyword in app_id_lower for keyword in ['snapshot', 'gnosis', 'aragon', 'dao']):
            return 'dao'
        
        else:
            return 'other'
    
    def _analyze_liquidity_provision(self, balances_data: List, apps_data: Dict) -> Dict[str, Any]:
        """Analyze liquidity provision activities"""
        
        lp_positions = []
        total_lp_value = 0
        lp_protocols = set()
        
        for balance_item in balances_data:
            # Check for LP indicators
            display_props = balance_item.get('displayProps', {})
            label = display_props.get('label', '').lower()
            
            if any(keyword in label for keyword in ['liquidity', 'lp', 'pool', 'pair', 'vault']):
                lp_value = balance_item.get('balanceUSD', 0)
                protocol = balance_item.get('appId', '')
                
                if lp_value > 0:
                    lp_positions.append({
                        'protocol': protocol,
                        'value_usd': lp_value,
                        'network': balance_item.get('network'),
                        'label': label,
                        'tokens': self._extract_lp_tokens(balance_item)
                    })
                    
                    total_lp_value += lp_value
                    lp_protocols.add(protocol)
        
        return {
            'total_lp_positions': len(lp_positions),
            'lp_positions_detail': lp_positions,
            'total_lp_value_usd': total_lp_value,
            'lp_protocols': list(lp_protocols),
            'lp_protocol_count': len(lp_protocols),
            'average_lp_size': total_lp_value / len(lp_positions) if lp_positions else 0
        }
    
    def _analyze_yield_farming_enhanced(self, balances_data: List, apps_data: Dict) -> Dict[str, Any]:
        """Enhanced yield farming analysis"""
        
        farming_positions = []
        farming_protocols = set()
        total_farming_value = 0
        
        # Known yield farming indicators
        farming_keywords = ['farm', 'chef', 'staking', 'reward', 'gauge', 'pool', 'vault']
        farming_protocols_list = ['yearn', 'harvest', 'pickle', 'convex', 'curve', 'beefy']
        
        for balance_item in balances_data:
            app_id = balance_item.get('appId', '').lower()
            label = balance_item.get('displayProps', {}).get('label', '').lower()
            balance_usd = balance_item.get('balanceUSD', 0)
            
            # Check if it's a farming position
            is_farming = (
                any(keyword in app_id for keyword in farming_protocols_list) or
                any(keyword in label for keyword in farming_keywords)
            )
            
            if is_farming and balance_usd > 0:
                farming_positions.append({
                    'protocol': app_id,
                    'value_usd': balance_usd,
                    'network': balance_item.get('network'),
                    'position_type': label
                })
                
                farming_protocols.add(app_id)
                total_farming_value += balance_usd
        
        return {
            'active_farming': len(farming_positions) > 0,
            'farming_positions': farming_positions,
            'farming_protocols': list(farming_protocols),
            'farming_protocol_count': len(farming_protocols),
            'total_farming_value_usd': total_farming_value,
            'farming_diversity_score': min(100, len(farming_protocols) * 20)
        }
    
    def _analyze_defi_risk_profile(self, balances_data: List, apps_data: Dict) -> Dict[str, Any]:
        """Analyze DeFi risk profile"""
        
        risk_factors = {
            'high_risk_protocols': 0,
            'medium_risk_protocols': 0,
            'low_risk_protocols': 0,
            'leverage_exposure': 0,
            'new_protocol_exposure': 0
        }
        
        # Risk categorization by protocol
        high_risk_protocols = ['alpha', 'rari', 'iron', 'tomb']  # Historical examples
        medium_risk_protocols = ['yearn', 'curve', 'convex']
        low_risk_protocols = ['aave', 'compound', 'uniswap', 'lido']
        
        total_value = 0
        high_risk_value = 0
        
        for balance_item in balances_data:
            app_id = balance_item.get('appId', '').lower()
            balance_usd = balance_item.get('balanceUSD', 0)
            total_value += balance_usd
            
            # Categorize risk
            if any(protocol in app_id for protocol in high_risk_protocols):
                risk_factors['high_risk_protocols'] += 1
                high_risk_value += balance_usd
            elif any(protocol in app_id for protocol in medium_risk_protocols):
                risk_factors['medium_risk_protocols'] += 1
            elif any(protocol in app_id for protocol in low_risk_protocols):
                risk_factors['low_risk_protocols'] += 1
        
        # Calculate risk score (0-100, lower is better)
        risk_score = 0
        if total_value > 0:
            high_risk_ratio = high_risk_value / total_value
            risk_score = min(100, high_risk_ratio * 100 + risk_factors['high_risk_protocols'] * 10)
        
        return {
            'risk_factors': risk_factors,
            'risk_score': risk_score,
            'high_risk_exposure_ratio': high_risk_value / total_value if total_value > 0 else 0,
            'risk_level': 'high' if risk_score > 60 else 'medium' if risk_score > 30 else 'low'
        }
    
    def _analyze_portfolio_composition(self, balances_data: List, tokens_data: List) -> Dict[str, Any]:
        """Analyze portfolio composition and asset allocation"""
        
        total_value = 0
        asset_types = {
            'defi_tokens': 0,
            'stablecoins': 0,
            'governance_tokens': 0,
            'lp_tokens': 0,
            'yield_tokens': 0
        }
        
        # Known token categories
        stablecoins = ['usdc', 'usdt', 'dai', 'busd', 'frax']
        governance_tokens = ['uni', 'sushi', 'comp', 'aave', 'crv', 'cvx']
        
        for balance_item in balances_data:
            balance_usd = balance_item.get('balanceUSD', 0)
            symbol = balance_item.get('symbol', '').lower()
            label = balance_item.get('displayProps', {}).get('label', '').lower()
            
            total_value += balance_usd
            
            # Categorize asset type
            if any(stable in symbol for stable in stablecoins):
                asset_types['stablecoins'] += balance_usd
            elif any(gov in symbol for gov in governance_tokens):
                asset_types['governance_tokens'] += balance_usd
            elif any(keyword in label for keyword in ['lp', 'pool', 'pair']):
                asset_types['lp_tokens'] += balance_usd
            elif any(keyword in label for keyword in ['vault', 'yield', 'farm']):
                asset_types['yield_tokens'] += balance_usd
            else:
                asset_types['defi_tokens'] += balance_usd
        
        # Calculate allocation percentages
        allocation_percentages = {}
        for asset_type, value in asset_types.items():
            allocation_percentages[asset_type] = (value / total_value * 100) if total_value > 0 else 0
        
        return {
            'total_portfolio_value': total_value,
            'asset_allocation_usd': asset_types,
            'asset_allocation_percentage': allocation_percentages,
            'portfolio_diversity': len([t for t in asset_types.values() if t > 0]),
            'stablecoin_ratio': allocation_percentages.get('stablecoins', 0) / 100
        }
    
    def _analyze_network_distribution(self, balances_data: List) -> Dict[str, Any]:
        """Analyze cross-network distribution"""
        
        network_distribution = {}
        network_values = {}
        
        for balance_item in balances_data:
            network = balance_item.get('network', 'unknown')
            balance_usd = balance_item.get('balanceUSD', 0)
            
            network_distribution[network] = network_distribution.get(network, 0) + 1
            network_values[network] = network_values.get(network, 0) + balance_usd
        
        total_value = sum(network_values.values())
        network_percentages = {
            network: (value / total_value * 100) if total_value > 0 else 0 
            for network, value in network_values.items()
        }
        
        return {
            'networks_used': list(network_distribution.keys()),
            'network_count': len(network_distribution),
            'position_distribution': network_distribution,
            'value_distribution_usd': network_values,
            'value_distribution_percentage': network_percentages,
            'cross_network_score': min(100, len(network_distribution) * 20)
        }
    
    def _calculate_enhanced_diversity_score(self, protocol_analysis: Dict) -> float:
        """Calculate enhanced diversity score"""
        
        protocol_count = protocol_analysis['unique_protocols_count']
        category_diversity = protocol_analysis['category_diversity']
        
        # Base score from protocol count (max 70 points)
        base_score = min(70, protocol_count * 5)
        
        # Category diversity bonus (max 30 points)
        category_bonus = min(30, category_diversity * 5)
        
        return min(100, base_score + category_bonus)
    
    def _calculate_interaction_depth_score(self, protocol_analysis: Dict, apps_data: Dict) -> float:
        """Calculate interaction depth score"""
        
        protocol_count = protocol_analysis['unique_protocols_count']
        category_count = protocol_analysis['category_diversity']
        
        # Base interaction score
        base_score = protocol_count * 8
        
        # Deep interaction bonus
        depth_bonus = category_count * 12
        
        # Apps interaction bonus
        apps_bonus = len(apps_data) * 5
        
        return min(200, base_score + depth_bonus + apps_bonus)
    
    def _calculate_defi_sophistication(self, protocol_analysis: Dict, yield_analysis: Dict, liquidity_analysis: Dict) -> int:
        """Calculate DeFi sophistication score"""
        
        sophistication = 0
        
        # Protocol sophistication
        if protocol_analysis['unique_protocols_count'] > 10:
            sophistication += 30
        elif protocol_analysis['unique_protocols_count'] > 5:
            sophistication += 20
        elif protocol_analysis['unique_protocols_count'] > 2:
            sophistication += 10
        
        # Category sophistication
        sophistication += protocol_analysis['category_diversity'] * 8
        
        # Yield farming sophistication
        if yield_analysis['active_farming']:
            sophistication += 20
            sophistication += yield_analysis['farming_protocol_count'] * 5
        
        # LP sophistication
        if liquidity_analysis['total_lp_positions'] > 0:
            sophistication += 15
            sophistication += min(15, liquidity_analysis['lp_protocol_count'] * 3)
        
        return min(100, sophistication)
    
    def _determine_experience_level(self, protocol_analysis: Dict, portfolio_analysis: Dict, sophistication_score: int) -> str:
        """Determine DeFi experience level"""
        
        protocols = protocol_analysis['unique_protocols_count']
        value = portfolio_analysis['total_portfolio_value']
        
        if protocols > 15 and value > 100000 and sophistication_score > 80:
            return 'expert'
        elif protocols > 8 and value > 50000 and sophistication_score > 60:
            return 'advanced'
        elif protocols > 3 and value > 10000 and sophistication_score > 40:
            return 'intermediate'
        elif protocols > 0 and sophistication_score > 20:
            return 'beginner'
        else:
            return 'newcomer'
    
    def _calculate_enhanced_data_quality(self, data_results: Dict) -> int:
        """Calculate enhanced data quality score"""
        
        quality_score = 0
        
        # Balance data quality (max 40 points)
        balances_result = data_results.get('balances', {})
        if balances_result.get('success'):
            balance_count = len(balances_result.get('data', []))
            quality_score += min(40, balance_count * 1.5)
        
        # Apps data quality (max 30 points)
        apps_result = data_results.get('apps', {})
        if apps_result.get('success'):
            apps_count = len(apps_result.get('data', {}))
            quality_score += min(30, apps_count * 5)
        
        # Token data quality (max 20 points)
        tokens_result = data_results.get('tokens', {})
        if tokens_result.get('success'):
            token_count = len(tokens_result.get('data', []))
            quality_score += min(20, token_count * 2)
        
        # NFT data quality (max 10 points)
        nft_result = data_results.get('nft_balances', {})
        if nft_result.get('success'):
            quality_score += 10
        
        return min(100, int(quality_score))
    
    # Helper methods
    def _extract_protocol_tokens(self, balance_item: Dict) -> List[Dict]:
        """Extract token information from protocol balance"""
        tokens = []
        if 'tokens' in balance_item:
            for token in balance_item['tokens']:
                tokens.append({
                    'symbol': token.get('symbol'),
                    'balance': token.get('balance'),
                    'balanceUSD': token.get('balanceUSD')
                })
        return tokens
    
    def _extract_lp_tokens(self, balance_item: Dict) -> List[str]:
        """Extract LP token pairs"""
        tokens = []
        if 'tokens' in balance_item:
            tokens = [token.get('symbol', '') for token in balance_item['tokens']]
        return tokens
    
    def _is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        return (
            isinstance(address, str) and
            address.startswith('0x') and
            len(address) == 42 and
            all(c in '0123456789abcdefABCDEF' for c in address[2:])
        )
    
    def _get_empty_defi_metrics(self) -> Dict[str, Any]:
        """Return comprehensive empty DeFi metrics structure"""
        return {
            'unique_protocols': 0,
            'total_balance_usd': 0.0,
            'lp_positions': 0,
            'diversity_score': 0.0,
            'interaction_depth': 0.0,
            'sophistication_score': 0,
            'protocol_analysis': {
                'unique_protocols_count': 0,
                'unique_protocols_list': [],
                'protocol_categories': {},
                'protocol_details': {},
                'total_protocol_value': 0,
                'category_diversity': 0
            },
            'liquidity_analysis': {
                'total_lp_positions': 0,
                'lp_positions_detail': [],
                'total_lp_value_usd': 0,
                'lp_protocols': [],
                'lp_protocol_count': 0
            },
            'yield_analysis': {
                'active_farming': False,
                'farming_positions': [],
                'farming_protocols': [],
                'farming_protocol_count': 0,
                'total_farming_value_usd': 0
            },
            'risk_analysis': {
                'risk_score': 0,
                'risk_level': 'low'
            },
            'portfolio_analysis': {
                'total_portfolio_value': 0,
                'asset_allocation_usd': {},
                'portfolio_diversity': 0
            },
            'network_analysis': {
                'networks_used': [],
                'network_count': 0,
                'cross_network_score': 0
            },
            'nft_holdings': 0,
            'defi_experience_level': 'newcomer',
            'data_quality_score': 0,
            'collection_timestamp': datetime.now().isoformat()
        }

# Test implementation
async def test_enhanced_zapper_client():
    """Comprehensive test for enhanced Zapper client"""
    
    client = ZapperClient()
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik's address
    
    try:
        print("🧪 Testing Enhanced Zapper Client...")
        print("=" * 50)
        
        metrics = await client.get_defi_metrics(test_address)
        
        print(f"✅ Address: {test_address}")
        print(f"✅ Unique Protocols: {metrics['unique_protocols']}")
        print(f"✅ Total Balance: ${metrics['total_balance_usd']:,.2f}")
        print(f"✅ LP Positions: {metrics['lp_positions']}")
        print(f"✅ Diversity Score: {metrics['diversity_score']:.1f}/100")
        print(f"✅ Sophistication Score: {metrics['sophistication_score']}/100")
        print(f"✅ Experience Level: {metrics['defi_experience_level']}")
        print(f"✅ Data Quality: {metrics['data_quality_score']}/100")
        
        print("\n📊 Protocol Categories:")
        for category, data in metrics['protocol_analysis']['protocol_categories'].items():
            if data['count'] > 0:
                print(f"   {category}: {data['count']} protocols (${data['value_usd']:,.2f})")
        
        print("\n📊 Detailed Results:")
        print(json.dumps(metrics, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error testing Zapper client: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_zapper_client())
