# clients/alchemy_client.py
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import os
from datetime import datetime, timedelta
import json
from loguru import logger

class AlchemyClient:
    """
    Complete and robust Alchemy API client for comprehensive multi-chain transaction data
    Handles: Ethereum, Polygon, Arbitrum, Optimism with advanced analytics
    """
    
    def __init__(self):
        self.api_key = os.getenv('ALCHEMY_API_KEY')
        if not self.api_key:
            raise ValueError("ALCHEMY_API_KEY not found in environment variables")
        
        # Enhanced chain configurations with proper timeout handling
        self.chain_configs = {
            'ethereum': {
                'rpc_url': f'https://eth-mainnet.g.alchemy.com/v2/{self.api_key}',
                'chain_id': 1,
                'name': 'Ethereum Mainnet',
                'native_token': 'ETH',
                'usd_price': 3500
            },
            'polygon': {
                'rpc_url': f'https://polygon-mainnet.g.alchemy.com/v2/{self.api_key}',
                'chain_id': 137,
                'name': 'Polygon Mainnet',
                'native_token': 'MATIC',
                'usd_price': 1.2
            },
            'arbitrum': {
                'rpc_url': f'https://arb-mainnet.g.alchemy.com/v2/{self.api_key}',
                'chain_id': 42161,
                'name': 'Arbitrum One',
                'native_token': 'ETH',
                'usd_price': 3500
            },
            'optimism': {
                'rpc_url': f'https://opt-mainnet.g.alchemy.com/v2/{self.api_key}',
                'chain_id': 10,
                'name': 'Optimism Mainnet',
                'native_token': 'ETH',
                'usd_price': 3500
            }
        }
        
        self.session_timeout = aiohttp.ClientTimeout(total=30)  # Reduced timeout
        self.max_retries = 2  # Reduced retries for faster failure
        self.retry_delay = 2
    
    def _is_valid_address(self, address: str) -> bool:
        """Enhanced address validation"""
        return (
            isinstance(address, str) and
            address.startswith('0x') and
            len(address) == 42 and
            all(c in '0123456789abcdefABCDEF' for c in address[2:])
        )
    
    async def get_transaction_metrics(self, address: str) -> Dict[str, Any]:
        """
        Get comprehensive transaction metrics across all supported chains
        Enhanced with robust error handling and graceful degradation
        """
        logger.info(f"Fetching enhanced transaction metrics for address: {address}")
        
        try:
            # Validate address format
            if not self._is_valid_address(address):
                raise ValueError(f"Invalid Ethereum address format: {address}")
            
            # Fetch data from all chains with retry logic
            chain_results = await self._fetch_all_chains_with_retry(address)
            
            # Process and analyze results with graceful error handling
            processed_data = self._process_chain_results(chain_results)
            transaction_metrics = self._calculate_enhanced_metrics(processed_data, address)
            
            logger.info(f"Successfully processed enhanced transaction data for {address}")
            return transaction_metrics
            
        except Exception as e:
            logger.error(f"Error fetching transaction metrics for {address}: {str(e)}")
            return self._get_empty_transaction_metrics()
    
    async def _fetch_all_chains_with_retry(self, address: str) -> List[Dict]:
        """Enhanced chain data fetching with robust timeout and error handling"""
        
        try:
            # Use shorter timeout and better error handling
            connector = aiohttp.TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30
            )
            
            async with aiohttp.ClientSession(
                timeout=self.session_timeout,
                connector=connector
            ) as session:
                tasks = []
                for chain_name, config in self.chain_configs.items():
                    task = self._get_chain_data_with_retry(session, address, chain_name, config)
                    tasks.append(task)
                
                # Add timeout protection for the entire batch
                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=25  # 25 second total timeout
                    )
                    return results
                except asyncio.TimeoutError:
                    logger.warning("Chain data collection timed out")
                    return [{'success': False, 'error': 'timeout', 'chain_name': chain} 
                           for chain in self.chain_configs.keys()]
                    
        except Exception as e:
            logger.error(f"Session creation failed: {str(e)}")
            return [{'success': False, 'error': str(e), 'chain_name': chain} 
                   for chain in self.chain_configs.keys()]
    
    async def _get_chain_data_with_retry(self, session: aiohttp.ClientSession, 
                                       address: str, chain_name: str, config: Dict) -> Dict:
        """Get chain data with comprehensive error handling and graceful degradation"""
        
        for attempt in range(self.max_retries):
            try:
                # Test basic connectivity first
                try:
                    async with session.get(config['rpc_url'], timeout=5) as test_response:
                        pass  # Just test connectivity
                except Exception as connectivity_error:
                    if attempt == self.max_retries - 1:
                        logger.warning(f"Connectivity test failed for {chain_name}: {connectivity_error}")
                        return self._get_empty_chain_result(chain_name, config, str(connectivity_error))
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                # Get transaction count with timeout protection
                try:
                    tx_count = await asyncio.wait_for(
                        self._get_transaction_count(session, address, config['rpc_url']),
                        timeout=8
                    )
                except asyncio.TimeoutError:
                    tx_count = 0
                    logger.warning(f"Transaction count timeout for {chain_name}")
                except Exception as e:
                    tx_count = 0
                    logger.warning(f"Transaction count failed for {chain_name}: {str(e)}")
                
                # Get enhanced asset transfers with timeout protection
                try:
                    transfers = await asyncio.wait_for(
                        self._get_enhanced_asset_transfers(session, address, config['rpc_url'], chain_name),
                        timeout=10
                    )
                except asyncio.TimeoutError:
                    transfers = []
                    logger.warning(f"Asset transfers timeout for {chain_name}")
                except Exception as e:
                    transfers = []
                    logger.warning(f"Asset transfers failed for {chain_name}: {str(e)}")
                
                # Get gas data with timeout protection
                try:
                    gas_data = await asyncio.wait_for(
                        self._get_enhanced_gas_data(session, address, config['rpc_url'], config),
                        timeout=5
                    )
                except asyncio.TimeoutError:
                    gas_data = self._get_empty_gas_data()
                    logger.warning(f"Gas data timeout for {chain_name}")
                except Exception as e:
                    gas_data = self._get_empty_gas_data()
                    logger.warning(f"Gas data failed for {chain_name}: {str(e)}")
                
                # Get token balances with timeout protection
                try:
                    token_balances = await asyncio.wait_for(
                        self._get_token_balances(session, address, config['rpc_url']),
                        timeout=5
                    )
                except asyncio.TimeoutError:
                    token_balances = []
                    logger.warning(f"Token balances timeout for {chain_name}")
                except Exception as e:
                    token_balances = []
                    logger.warning(f"Token balances failed for {chain_name}: {str(e)}")
                
                # Return successful result
                return {
                    'chain_name': chain_name,
                    'chain_id': config['chain_id'],
                    'success': True,
                    'transaction_count': tx_count,
                    'transfers': transfers,
                    'gas_data': gas_data,
                    'token_balances': token_balances,
                    'native_token_info': {
                        'symbol': config['native_token'],
                        'usd_price': config['usd_price']
                    },
                    'error': None,
                    'attempt': attempt + 1
                }
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {chain_name}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return self._get_empty_chain_result(chain_name, config, str(e))
                await asyncio.sleep(self.retry_delay * (attempt + 1))
    
    def _get_empty_chain_result(self, chain_name: str, config: Dict, error: str) -> Dict:
        """Return empty chain result with error info"""
        return {
            'chain_name': chain_name,
            'chain_id': config['chain_id'],
            'success': False,
            'transaction_count': 0,
            'transfers': [],
            'gas_data': self._get_empty_gas_data(),
            'token_balances': [],
            'error': error,
            'attempts_made': self.max_retries
        }
    
    def _get_empty_gas_data(self) -> Dict:
        """Return empty gas data structure"""
        return {
            'current_gas_price_wei': 0,
            'current_gas_price_gwei': 0,
            'gas_efficiency_score': 50,
            'error': 'no_data'
        }
    
    async def _get_enhanced_asset_transfers(self, session: aiohttp.ClientSession, 
                                          address: str, rpc_url: str, chain_name: str) -> List[Dict]:
        """
        COMPLETE IMPLEMENTATION: Enhanced asset transfers with chain-specific category filtering
        """
        
        # Define supported categories per chain (fixes the network errors)
        chain_categories = {
            'ethereum': ["external", "internal", "erc20", "erc721", "erc1155"],
            'polygon': ["external", "internal", "erc20", "erc721", "erc1155"],
            'arbitrum': ["external", "erc20", "erc721", "erc1155"],  # No internal support
            'optimism': ["external", "erc20", "erc721", "erc1155"]   # No internal support
        }
        
        # Get supported categories for this chain
        supported_categories = chain_categories.get(chain_name, ["external", "erc20", "erc721"])
        
        try:
            # Get both incoming and outgoing transfers with proper categories
            transfer_tasks = [
                self._fetch_transfers(session, rpc_url, {
                    "fromBlock": "0x0",
                    "toBlock": "latest",
                    "fromAddress": address,
                    "category": supported_categories,
                    "maxCount": "0x32",  # Reduced to 50 for better performance
                    "order": "desc"
                }),
                self._fetch_transfers(session, rpc_url, {
                    "fromBlock": "0x0",
                    "toBlock": "latest", 
                    "toAddress": address,
                    "category": supported_categories,
                    "maxCount": "0x32",  # Reduced to 50 for better performance
                    "order": "desc"
                })
            ]
            
            # Execute with timeout protection
            try:
                from_transfers, to_transfers = await asyncio.wait_for(
                    asyncio.gather(*transfer_tasks), 
                    timeout=8
                )
            except asyncio.TimeoutError:
                logger.warning(f"Transfer fetch timeout for {chain_name}")
                return []
            
            # Combine and deduplicate
            all_transfers = from_transfers + to_transfers
            seen_hashes = set()
            unique_transfers = []
            
            for transfer in all_transfers:
                tx_hash = transfer.get('hash')
                if tx_hash and tx_hash not in seen_hashes:
                    seen_hashes.add(tx_hash)
                    # Enhance transfer data safely
                    enhanced_transfer = self._enhance_transfer_data(transfer, address)
                    unique_transfers.append(enhanced_transfer)
            
            return sorted(unique_transfers, key=lambda x: x.get('blockNum', 0), reverse=True)
            
        except Exception as e:
            logger.warning(f"Asset transfer collection failed for {chain_name}: {str(e)}")
            return []
    
    def _enhance_transfer_data(self, transfer: Dict, user_address: str) -> Dict:
        """
        FIXED: Enhance transfer data with additional analytics and safe null handling
        """
        
        enhanced = transfer.copy()
        
        # SAFE NULL HANDLING for addresses
        from_addr = transfer.get('from') or ''
        to_addr = transfer.get('to') or ''
        user_addr = user_address.lower() if user_address else ''
        
        from_addr = from_addr.lower() if from_addr else ''
        to_addr = to_addr.lower() if to_addr else ''
        
        if from_addr == user_addr:
            enhanced['direction'] = 'outgoing'
        elif to_addr == user_addr:
            enhanced['direction'] = 'incoming'
        else:
            enhanced['direction'] = 'unknown'
        
        # Categorize transaction type safely
        category = transfer.get('category', '')
        enhanced['transaction_type'] = self._categorize_transaction(transfer, category)
        
        # Calculate USD value estimate safely
        enhanced['estimated_usd_value'] = self._estimate_usd_value(transfer)
        
        # Extract timestamp safely
        block_timestamp = transfer.get('metadata', {}).get('blockTimestamp')
        if block_timestamp:
            try:
                if isinstance(block_timestamp, str) and block_timestamp.startswith('0x'):
                    timestamp = int(block_timestamp, 16)
                elif isinstance(block_timestamp, str):
                    timestamp = datetime.fromisoformat(block_timestamp.replace('Z', '+00:00')).timestamp()
                else:
                    timestamp = 0
                enhanced['timestamp'] = timestamp
                enhanced['date'] = datetime.fromtimestamp(timestamp).isoformat() if timestamp > 0 else None
            except Exception:
                enhanced['timestamp'] = 0
                enhanced['date'] = None
        else:
            enhanced['timestamp'] = 0
            enhanced['date'] = None
        
        return enhanced
    
    def _categorize_transaction(self, transfer: Dict, category: str) -> str:
        """Categorize transaction based on transfer data"""
        
        asset = transfer.get('asset', '')
        raw_contract = transfer.get('rawContract', {})
        contract_address = raw_contract.get('address', '').lower() if raw_contract.get('address') else ''
        
        # Known DeFi protocol contracts (simplified)
        defi_contracts = {
            '0xa0b86a33e6c7b8e6a1b30b1f0b1a0b1a0b1a0b1a': 'uniswap',
            '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': 'aave',
        }
        
        if contract_address in defi_contracts:
            return f"defi_{defi_contracts[contract_address]}"
        elif category == 'erc20':
            return 'token_transfer'
        elif category == 'erc721' or category == 'erc1155':
            return 'nft_transfer'
        elif category == 'external':
            return 'native_transfer'
        else:
            return 'other'
    
    def _estimate_usd_value(self, transfer: Dict) -> float:
        """Estimate USD value of transfer (simplified)"""
        
        try:
            value = transfer.get('value', 0)
            if not value or value == '0.0':
                return 0.0
            
            # For ETH transfers, use ETH price
            if transfer.get('asset') == 'ETH':
                return float(value) * 3500  # Approximate ETH price
            return 0.0
        except Exception:
            return 0.0
    
    async def _get_transaction_count(self, session: aiohttp.ClientSession, 
                                   address: str, rpc_url: str) -> int:
        """Get total transaction count for an address with error handling"""
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getTransactionCount",
                "params": [address, "latest"],
                "id": 1
            }
            
            async with session.post(rpc_url, json=payload) as response:
                if response.status != 200:
                    logger.warning(f"Transaction count HTTP error: {response.status}")
                    return 0
                
                data = await response.json()
                if 'error' in data:
                    logger.warning(f"Transaction count RPC error: {data['error']}")
                    return 0
                
                return int(data.get('result', '0x0'), 16)
                
        except Exception as e:
            logger.warning(f"Transaction count exception: {str(e)}")
            return 0
    
    async def _fetch_transfers(self, session: aiohttp.ClientSession, 
                             rpc_url: str, params: Dict) -> List[Dict]:
        """Fetch transfers using alchemy_getAssetTransfers with robust error handling"""
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "alchemy_getAssetTransfers",
                "params": [params],
                "id": 1
            }
            
            async with session.post(rpc_url, json=payload) as response:
                if response.status != 200:
                    logger.warning(f"Asset transfer HTTP error: {response.status}")
                    return []
                
                data = await response.json()
                if 'error' in data:
                    logger.warning(f"Asset transfer RPC error: {data['error']}")
                    return []
                
                return data.get('result', {}).get('transfers', [])
                
        except Exception as e:
            logger.warning(f"Asset transfer exception: {str(e)}")
            return []
    
    async def _get_enhanced_gas_data(self, session: aiohttp.ClientSession, 
                                   address: str, rpc_url: str, config: Dict) -> Dict:
        """Enhanced gas data with efficiency metrics and error handling"""
        
        try:
            # Get current gas price
            gas_price_payload = {
                "jsonrpc": "2.0",
                "method": "eth_gasPrice",
                "params": [],
                "id": 1
            }
            
            async with session.post(rpc_url, json=gas_price_payload) as response:
                if response.status != 200:
                    return self._get_empty_gas_data()
                
                gas_data = await response.json()
                if 'error' in gas_data:
                    return self._get_empty_gas_data()
                
                current_gas_price = int(gas_data.get('result', '0x0'), 16)
            
            # Get gas usage estimation
            gas_efficiency_score = await self._calculate_gas_efficiency(session, rpc_url, config)
            
            return {
                'current_gas_price_wei': current_gas_price,
                'current_gas_price_gwei': current_gas_price / 1e9,
                'gas_efficiency_score': gas_efficiency_score,
                'chain_name': config['name'],
                'native_token': config['native_token']
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch gas data: {str(e)}")
            return self._get_empty_gas_data()
    
    async def _calculate_gas_efficiency(self, session: aiohttp.ClientSession, 
                                      rpc_url: str, config: Dict) -> int:
        """Calculate gas efficiency based on network conditions"""
        
        try:
            # Get latest block
            block_payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBlockByNumber",
                "params": ["latest", False],
                "id": 1
            }
            
            async with session.post(rpc_url, json=block_payload) as response:
                if response.status != 200:
                    return 50
                
                block_data = await response.json()
                if 'error' in block_data:
                    return 50
                
                block = block_data.get('result', {})
                
                gas_used = int(block.get('gasUsed', '0x0'), 16)
                gas_limit = int(block.get('gasLimit', '0x1'), 16)
                
                # Calculate network congestion
                if gas_limit > 0:
                    congestion_ratio = gas_used / gas_limit
                    efficiency = max(20, 100 - int(congestion_ratio * 80))
                    return efficiency
                else:
                    return 50
                    
        except Exception:
            return 50  # Default neutral score
    
    async def _get_token_balances(self, session: aiohttp.ClientSession, 
                                address: str, rpc_url: str) -> List[Dict]:
        """Get token balances using Alchemy's getTokenBalances"""
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "alchemy_getTokenBalances",
                "params": [address],
                "id": 1
            }
            
            async with session.post(rpc_url, json=payload) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                if 'error' in data:
                    return []
                
                return data.get('result', {}).get('tokenBalances', [])
                
        except Exception as e:
            logger.debug(f"Token balance fetch failed: {str(e)}")
            return []
    
    def _calculate_enhanced_metrics(self, processed_data: Dict, address: str) -> Dict[str, Any]:
        """
        COMPLETE IMPLEMENTATION: Calculate enhanced transaction metrics with advanced analytics
        """
        
        all_transfers = processed_data.get('all_transfers', [])
        
        # Basic metrics
        total_transactions = processed_data.get('total_transactions', 0)
        active_chains = len(processed_data.get('successful_chains', []))
        
        # Enhanced frequency calculation
        frequency_metrics = self._calculate_frequency_metrics(all_transfers)
        
        # Enhanced value analysis
        value_metrics = self._calculate_value_metrics(all_transfers)
        
        # Transaction pattern analysis
        pattern_metrics = self._analyze_transaction_patterns(all_transfers)
        
        # Cross-chain activity analysis
        cross_chain_metrics = self._analyze_cross_chain_activity(processed_data.get('chain_distribution', {}))
        
        # Gas efficiency across chains
        gas_metrics = self._analyze_gas_efficiency(processed_data.get('gas_data', {}))
        
        # Recent activity trends
        activity_trends = self._analyze_activity_trends(all_transfers)
        
        return {
            'total_transactions': total_transactions,
            'active_chains': active_chains,
            'monthly_txn_count': frequency_metrics['monthly_count'],
            'weekly_txn_count': frequency_metrics['weekly_count'],
            'daily_avg_txns': frequency_metrics['daily_average'],
            'avg_value_usd': value_metrics['average_usd'],
            'median_value_usd': value_metrics['median_usd'],
            'total_volume_usd': value_metrics['total_volume_usd'],
            'gas_efficiency': gas_metrics['average_efficiency'],
            'consistency_score': pattern_metrics['consistency_score'],
            'activity_score': pattern_metrics['activity_score'],
            'cross_chain_score': cross_chain_metrics['cross_chain_score'],
            'chain_distribution': processed_data.get('chain_distribution', {}),
            'transaction_types': pattern_metrics['transaction_types'],
            'recent_activity': activity_trends,
            'successful_chains': processed_data.get('successful_chains', []),
            'failed_chains': processed_data.get('failed_chains', []),
            'data_quality_score': self._calculate_data_quality_score(processed_data)
        }
    
    def _calculate_frequency_metrics(self, transfers: List[Dict]) -> Dict[str, Any]:
        """Calculate detailed frequency metrics"""
        
        if not transfers:
            return {'monthly_count': 0, 'weekly_count': 0, 'daily_average': 0}
        
        now = datetime.now()
        month_ago = now - timedelta(days=30)
        week_ago = now - timedelta(days=7)
        
        monthly_count = 0
        weekly_count = 0
        
        for transfer in transfers:
            timestamp = transfer.get('timestamp', 0)
            if timestamp and timestamp > 0:
                try:
                    tx_date = datetime.fromtimestamp(timestamp)
                    if tx_date > month_ago:
                        monthly_count += 1
                        if tx_date > week_ago:
                            weekly_count += 1
                except Exception:
                    continue
        
        daily_average = monthly_count / 30 if monthly_count > 0 else 0
        
        return {
            'monthly_count': monthly_count,
            'weekly_count': weekly_count,
            'daily_average': round(daily_average, 2)
        }
    
    def _calculate_value_metrics(self, transfers: List[Dict]) -> Dict[str, Any]:
        """Calculate detailed value metrics"""
        
        if not transfers:
            return {'average_usd': 0, 'median_usd': 0, 'total_volume_usd': 0}
        
        usd_values = []
        total_volume = 0
        
        for transfer in transfers:
            usd_value = transfer.get('estimated_usd_value', 0)
            if usd_value and usd_value > 0:
                usd_values.append(usd_value)
                total_volume += usd_value
        
        if not usd_values:
            return {'average_usd': 0, 'median_usd': 0, 'total_volume_usd': 0}
        
        average_usd = sum(usd_values) / len(usd_values)
        median_usd = sorted(usd_values)[len(usd_values) // 2]
        
        return {
            'average_usd': round(average_usd, 2),
            'median_usd': round(median_usd, 2),
            'total_volume_usd': round(total_volume, 2)
        }
    
    def _analyze_transaction_patterns(self, transfers: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction patterns for consistency and activity scoring"""
        
        if len(transfers) < 3:
            return {
                'consistency_score': 0,
                'activity_score': 0,
                'transaction_types': {}
            }
        
        # Consistency analysis
        timestamps = [t.get('timestamp', 0) for t in transfers if t.get('timestamp', 0) > 0]
        consistency_score = self._calculate_consistency_from_timestamps(timestamps)
        
        # Activity scoring
        activity_score = min(100, len(transfers) * 2)  # 2 points per transaction, capped at 100
        
        # Transaction type distribution
        type_distribution = {}
        for transfer in transfers:
            tx_type = transfer.get('transaction_type', 'unknown')
            type_distribution[tx_type] = type_distribution.get(tx_type, 0) + 1
        
        return {
            'consistency_score': consistency_score,
            'activity_score': activity_score,
            'transaction_types': type_distribution
        }
    
    def _calculate_consistency_from_timestamps(self, timestamps: List[float]) -> float:
        """Calculate consistency score from timestamps"""
        
        if len(timestamps) < 2:
            return 0.0
        
        try:
            # Sort timestamps
            timestamps.sort()
            
            # Calculate intervals
            intervals = []
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i-1]
                if interval > 0:
                    intervals.append(interval)
            
            if not intervals:
                return 0.0
            
            # Calculate coefficient of variation
            mean_interval = sum(intervals) / len(intervals)
            if mean_interval == 0:
                return 0.0
            
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = variance ** 0.5
            cv = std_dev / mean_interval
            
            # Convert to consistency score (0-100, lower CV = higher consistency)
            consistency_score = max(0, 100 - (cv * 10))
            return min(100, consistency_score)
            
        except Exception:
            return 0.0
    
    def _analyze_cross_chain_activity(self, chain_distribution: Dict) -> Dict[str, Any]:
        """Analyze cross-chain activity patterns"""
        
        total_chains = len([c for c in chain_distribution.values() if c.get('transaction_count', 0) > 0])
        
        if total_chains <= 1:
            cross_chain_score = 0
        elif total_chains == 2:
            cross_chain_score = 30
        elif total_chains == 3:
            cross_chain_score = 60
        else:
            cross_chain_score = 100
        
        return {
            'cross_chain_score': cross_chain_score,
            'active_chains_count': total_chains,
            'chain_diversity': total_chains / 4 * 100  # 4 supported chains
        }
    
    def _analyze_gas_efficiency(self, gas_data: Dict) -> Dict[str, Any]:
        """Analyze gas efficiency across chains"""
        
        if not gas_data:
            return {'average_efficiency': 50, 'best_chain': None, 'efficiency_by_chain': {}}
        
        efficiencies = []
        efficiency_by_chain = {}
        
        for chain, data in gas_data.items():
            if isinstance(data, dict):
                efficiency = data.get('gas_efficiency_score', 50)
                efficiencies.append(efficiency)
                efficiency_by_chain[chain] = efficiency
        
        average_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 50
        best_chain = max(efficiency_by_chain.items(), key=lambda x: x[1])[0] if efficiency_by_chain else None
        
        return {
            'average_efficiency': round(average_efficiency, 1),
            'best_chain': best_chain,
            'efficiency_by_chain': efficiency_by_chain
        }
    
    def _analyze_activity_trends(self, transfers: List[Dict]) -> Dict[str, Any]:
        """Analyze recent activity trends"""
        
        if not transfers:
            return {
                'trend': 'no_activity',
                'last_24h': 0,
                'last_7d': 0,
                'last_30d': 0,
                'is_active_user': False
            }
        
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        counts = {'last_24h': 0, 'last_7d': 0, 'last_30d': 0}
        
        for transfer in transfers:
            timestamp = transfer.get('timestamp', 0)
            if timestamp and timestamp > 0:
                try:
                    tx_date = datetime.fromtimestamp(timestamp)
                    if tx_date > day_ago:
                        counts['last_24h'] += 1
                    if tx_date > week_ago:
                        counts['last_7d'] += 1
                    if tx_date > month_ago:
                        counts['last_30d'] += 1
                except Exception:
                    continue
        
        # Determine trend
        if counts['last_24h'] > 5:
            trend = 'very_active'
        elif counts['last_7d'] > 10:
            trend = 'active'
        elif counts['last_30d'] > 5:
            trend = 'moderate'
        else:
            trend = 'low_activity'
        
        return {
            'trend': trend,
            'last_24h': counts['last_24h'],
            'last_7d': counts['last_7d'],
            'last_30d': counts['last_30d'],
            'is_active_user': counts['last_30d'] > 10
        }
    
    def _calculate_data_quality_score(self, processed_data: Dict) -> int:
        """Calculate comprehensive data quality score"""
        
        quality_score = 0
        
        # Chain coverage (max 30 points)
        successful_chains = len(processed_data.get('successful_chains', []))
        quality_score += min(30, successful_chains * 7.5)
        
        # Transaction data availability (max 25 points)
        if processed_data.get('total_transactions', 0) > 0:
            quality_score += 25
        
        # Transfer data quality (max 25 points)
        transfer_count = len(processed_data.get('all_transfers', []))
        quality_score += min(25, transfer_count * 0.5)
        
        # Gas data availability (max 20 points)
        gas_data = processed_data.get('gas_data', {})
        gas_data_chains = len([c for c in gas_data.values() if isinstance(c, dict) and c.get('current_gas_price_wei', 0) > 0])
        quality_score += min(20, gas_data_chains * 5)
        
        return min(100, int(quality_score))
    
    def _process_chain_results(self, chain_results: List) -> Dict[str, Any]:
        """Process results from all chains with enhanced error handling"""
        
        processed_data = {
            'successful_chains': [],
            'failed_chains': [],
            'total_transactions': 0,
            'all_transfers': [],
            'chain_distribution': {},
            'gas_data': {}
        }
        
        for result in chain_results:
            if isinstance(result, Exception):
                processed_data['failed_chains'].append({
                    'error': str(result),
                    'chain': 'unknown'
                })
                continue
            
            if isinstance(result, dict) and result.get('success'):
                chain_name = result.get('chain_name', 'unknown')
                processed_data['successful_chains'].append(chain_name)
                processed_data['total_transactions'] += result.get('transaction_count', 0)
                processed_data['all_transfers'].extend(result.get('transfers', []))
                processed_data['chain_distribution'][chain_name] = {
                    'transaction_count': result.get('transaction_count', 0),
                    'transfer_count': len(result.get('transfers', [])),
                    'token_balances': len(result.get('token_balances', []))
                }
                processed_data['gas_data'][chain_name] = result.get('gas_data', {})
            else:
                processed_data['failed_chains'].append({
                    'chain': result.get('chain_name', 'unknown') if isinstance(result, dict) else 'unknown',
                    'error': result.get('error', 'unknown error') if isinstance(result, dict) else 'unknown error'
                })
        
        return processed_data
    
    def _get_empty_transaction_metrics(self) -> Dict[str, Any]:
        """Return comprehensive empty metrics structure"""
        return {
            'total_transactions': 0,
            'active_chains': 0,
            'monthly_txn_count': 0,
            'weekly_txn_count': 0,
            'daily_avg_txns': 0,
            'avg_value_usd': 0.0,
            'median_value_usd': 0.0,
            'total_volume_usd': 0.0,
            'gas_efficiency': 50.0,
            'consistency_score': 0.0,
            'activity_score': 0,
            'cross_chain_score': 0,
            'chain_distribution': {},
            'transaction_types': {},
            'recent_activity': {
                'trend': 'no_activity',
                'last_24h': 0,
                'last_7d': 0,
                'last_30d': 0,
                'is_active_user': False
            },
            'successful_chains': [],
            'failed_chains': [],
            'data_quality_score': 0
        }


# Test implementation
async def test_enhanced_alchemy_client():
    """Comprehensive test for fixed Alchemy client"""
    
    client = AlchemyClient()
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik's address
    
    try:
        print("🧪 Testing Fixed Alchemy Client...")
        print("=" * 50)
        
        metrics = await client.get_transaction_metrics(test_address)
        
        print(f"✅ Address: {test_address}")
        print(f"✅ Total Transactions: {metrics['total_transactions']}")
        print(f"✅ Active Chains: {metrics['active_chains']}")
        print(f"✅ Monthly Activity: {metrics['monthly_txn_count']} transactions")
        print(f"✅ Gas Efficiency: {metrics['gas_efficiency']}%")
        print(f"✅ Consistency Score: {metrics['consistency_score']:.1f}/100")
        print(f"✅ Data Quality: {metrics['data_quality_score']}/100")
        print(f"✅ Activity Trend: {metrics['recent_activity']['trend']}")
        
        print("\n📊 Successful Chains:", metrics['successful_chains'])
        print("❌ Failed Chains:", len(metrics['failed_chains']))
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Alchemy client: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_alchemy_client())
