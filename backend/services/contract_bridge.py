# backend/services/contract_bridge.py

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import Web3Exception
from eth_account import Account
from eth_typing import Address
import json
from dataclasses import dataclass
from datetime import datetime, timezone
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BehavioralMetrics:
    """Behavioral metrics structure matching the smart contract"""
    transactionFrequency: int
    averageTransactionValue: int
    gasEfficiencyScore: int
    crossChainActivityCount: int
    consistencyMetric: int
    protocolInteractionCount: int
    totalDeFiBalanceUSD: int
    liquidityPositionCount: int
    protocolDiversityScore: int
    totalStakedUSD: int
    stakingDurationDays: int
    stakingPlatformCount: int
    rewardClaimFrequency: int
    liquidationEventCount: int
    leverageRatio: int
    portfolioVolatility: int
    stakingLoyaltyScore: int
    interactionDepthScore: int
    yieldFarmingActive: int
    accountAgeScore: int
    activityConsistencyScore: int
    engagementScore: int

@dataclass
class CreditScore:
    """Credit score structure matching the smart contract"""
    totalScore: int
    transactionScore: int
    defiScore: int
    stakingScore: int
    riskScore: int
    historyScore: int
    lastUpdated: int
    confidence: int
    updateCount: int
    isActive: bool

class ContractBridge:
    """
    Bridge service to interact with the deployed CVCP protocol smart contracts on Scroll Sepolia
    Handles all contract interactions for behavioral data updates and credit score calculations
    """
    
    def __init__(self):
        """Initialize the contract bridge with environment configuration"""
        self.w3 = None
        self.account = None
        self.registry_contract = None
        self.registry_address = "0x8e9288aD536Ee22Df91026BE96cB1deE904C05eF"  # Deployed contract
        self.chain_id = 534351  # Scroll Sepolia
        
        # Load configuration from environment
        self._load_config()
        self._setup_web3()
        self._setup_contract()
        
    def _load_config(self):
        """Load configuration from environment variables"""
        # Network configuration
        self.rpc_url = os.getenv(
            'SCROLL_SEPOLIA_RPC', 
            'https://scroll-sepolia.g.alchemy.com/v2/FKj-Ao97HOyiDsdSHZ3ED'
        )
        
        # Wallet configuration
        self.private_key = os.getenv('SCROLL_SEPOLIA_PRIVATE_KEY')
        if not self.private_key:
            raise ValueError("SCROLL_SEPOLIA_PRIVATE_KEY environment variable is required")
            
        # Gas configuration
        self.gas_price = int(os.getenv('SCROLL_SEPOLIA_GAS_PRICE', '100000000'))  # 0.1 gwei
        self.gas_limit = int(os.getenv('SCROLL_SEPOLIA_GAS_LIMIT', '500000'))
        
        # Protocol configuration
        self.min_update_interval = int(os.getenv('MINIMUM_UPDATE_INTERVAL', '1800'))  # 30 minutes
        
        logger.info(f"Loaded config - RPC: {self.rpc_url}, Chain ID: {self.chain_id}")
        
    def _setup_web3(self):
        """Setup Web3 connection with proper middleware"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Add middleware for Scroll Sepolia (POA network)
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Setup account
            self.account = Account.from_key(self.private_key)
            
            # Test connection
            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to Scroll Sepolia")
                
            latest_block = self.w3.eth.get_block('latest')
            logger.info(f"Connected to Scroll Sepolia - Latest block: {latest_block.number}")
            logger.info(f"Using account: {self.account.address}")
            
            # Check balance
            balance = self.w3.eth.get_balance(self.account.address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            logger.info(f"Account balance: {balance_eth:.4f} ETH")
            
            if balance_eth < 0.001:
                logger.warning("Low account balance - may not be sufficient for transactions")
                
        except Exception as e:
            logger.error(f"Failed to setup Web3: {e}")
            raise
            
    def _setup_contract(self):
        """Setup contract interface using the deployed contract ABI"""
        try:
            # Load the contract ABI from the deployment artifacts
            contract_abi = self._get_contract_abi()
            
            # Create contract instance
            self.registry_contract = self.w3.eth.contract(
                address=self.registry_address,
                abi=contract_abi
            )
            
            # Test contract connection
            protocol_version = self.registry_contract.functions.PROTOCOL_VERSION().call()
            owner = self.registry_contract.functions.owner().call()
            
            logger.info(f"Contract connected - Version: {protocol_version}, Owner: {owner}")
            logger.info(f"Contract address: {self.registry_address}")
            
            # Verify authorization
            is_authorized = self.registry_contract.functions.authorizedDataProviders(self.account.address).call()
            logger.info(f"Data provider authorized: {is_authorized}")
            
            if not is_authorized:
                logger.warning("Account is not authorized as a data provider")
                
        except Exception as e:
            logger.error(f"Failed to setup contract: {e}")
            raise
    
    def _get_contract_abi(self) -> List[Dict]:
        """Get the contract ABI from deployment artifacts or define it manually"""
        # Contract ABI for CreditScoreRegistry (key functions only)
        return [
            {
                "inputs": [{"internalType": "address", "name": "initialOwner", "type": "address"}],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "inputs": [],
                "name": "PROTOCOL_VERSION",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "owner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "", "type": "address"}],
                "name": "authorizedDataProviders",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "user", "type": "address"},
                    {
                        "components": [
                            {"internalType": "uint256", "name": "transactionFrequency", "type": "uint256"},
                            {"internalType": "uint256", "name": "averageTransactionValue", "type": "uint256"},
                            {"internalType": "uint256", "name": "gasEfficiencyScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "crossChainActivityCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "consistencyMetric", "type": "uint256"},
                            {"internalType": "uint256", "name": "protocolInteractionCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "totalDeFiBalanceUSD", "type": "uint256"},
                            {"internalType": "uint256", "name": "liquidityPositionCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "protocolDiversityScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "totalStakedUSD", "type": "uint256"},
                            {"internalType": "uint256", "name": "stakingDurationDays", "type": "uint256"},
                            {"internalType": "uint256", "name": "stakingPlatformCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "rewardClaimFrequency", "type": "uint256"},
                            {"internalType": "uint256", "name": "liquidationEventCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "leverageRatio", "type": "uint256"},
                            {"internalType": "uint256", "name": "portfolioVolatility", "type": "uint256"},
                            {"internalType": "uint256", "name": "stakingLoyaltyScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "interactionDepthScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "yieldFarmingActive", "type": "uint256"},
                            {"internalType": "uint256", "name": "accountAgeScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "activityConsistencyScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "engagementScore", "type": "uint256"}
                        ],
                        "internalType": "struct ProtocolMath.BehavioralMetrics",
                        "name": "metrics",
                        "type": "tuple"
                    }
                ],
                "name": "updateBehavioralData",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "calculateCreditScore",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "getCreditScore",
                "outputs": [
                    {
                        "components": [
                            {"internalType": "uint256", "name": "totalScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "transactionScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "defiScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "stakingScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "riskScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "historyScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "lastUpdated", "type": "uint256"},
                            {"internalType": "uint256", "name": "confidence", "type": "uint256"},
                            {"internalType": "uint256", "name": "updateCount", "type": "uint256"},
                            {"internalType": "bool", "name": "isActive", "type": "bool"}
                        ],
                        "internalType": "struct CreditScoreRegistry.CreditScore",
                        "name": "",
                        "type": "tuple"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "components": [
                            {"internalType": "uint256", "name": "transactionFrequency", "type": "uint256"},
                            {"internalType": "uint256", "name": "averageTransactionValue", "type": "uint256"},
                            {"internalType": "uint256", "name": "gasEfficiencyScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "crossChainActivityCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "consistencyMetric", "type": "uint256"},
                            {"internalType": "uint256", "name": "protocolInteractionCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "totalDeFiBalanceUSD", "type": "uint256"},
                            {"internalType": "uint256", "name": "liquidityPositionCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "protocolDiversityScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "totalStakedUSD", "type": "uint256"},
                            {"internalType": "uint256", "name": "stakingDurationDays", "type": "uint256"},
                            {"internalType": "uint256", "name": "stakingPlatformCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "rewardClaimFrequency", "type": "uint256"},
                            {"internalType": "uint256", "name": "liquidationEventCount", "type": "uint256"},
                            {"internalType": "uint256", "name": "leverageRatio", "type": "uint256"},
                            {"internalType": "uint256", "name": "portfolioVolatility", "type": "uint256"},
                            {"internalType": "uint256", "name": "stakingLoyaltyScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "interactionDepthScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "yieldFarmingActive", "type": "uint256"},
                            {"internalType": "uint256", "name": "accountAgeScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "activityConsistencyScore", "type": "uint256"},
                            {"internalType": "uint256", "name": "engagementScore", "type": "uint256"}
                        ],
                        "internalType": "struct ProtocolMath.BehavioralMetrics",
                        "name": "metrics",
                        "type": "tuple"
                    }
                ],
                "name": "previewScore",
                "outputs": [
                    {"internalType": "uint256", "name": "estimatedScore", "type": "uint256"},
                    {"internalType": "uint256", "name": "confidence", "type": "uint256"}
                ],
                "stateMutability": "pure",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "getScoreHistory",
                "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def _convert_metrics_to_tuple(self, metrics: BehavioralMetrics) -> tuple:
        """Convert BehavioralMetrics to tuple for contract call"""
        return (
            metrics.transactionFrequency,
            metrics.averageTransactionValue,
            metrics.gasEfficiencyScore,
            metrics.crossChainActivityCount,
            metrics.consistencyMetric,
            metrics.protocolInteractionCount,
            metrics.totalDeFiBalanceUSD,
            metrics.liquidityPositionCount,
            metrics.protocolDiversityScore,
            metrics.totalStakedUSD,
            metrics.stakingDurationDays,
            metrics.stakingPlatformCount,
            metrics.rewardClaimFrequency,
            metrics.liquidationEventCount,
            metrics.leverageRatio,
            metrics.portfolioVolatility,
            metrics.stakingLoyaltyScore,
            metrics.interactionDepthScore,
            metrics.yieldFarmingActive,
            metrics.accountAgeScore,
            metrics.activityConsistencyScore,
            metrics.engagementScore
        )
    
    def _build_transaction(self, function_call, gas_limit: Optional[int] = None) -> Dict:
        """Build a transaction with proper gas settings"""
        nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
        
        # Get current gas price with buffer
        current_gas_price = self.w3.eth.gas_price
        gas_price = max(current_gas_price * 110 // 100, self.gas_price)  # 10% buffer
        
        transaction = function_call.build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'gas': gas_limit or self.gas_limit,
            'gasPrice': gas_price,
            'chainId': self.chain_id
        })
        
        return transaction
    
    def _send_transaction(self, transaction: Dict) -> str:
        """Sign and send transaction"""
        try:
            # Sign transaction
            signed_transaction = self.account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"Transaction sent: {tx_hash_hex}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                logger.info(f"Transaction confirmed: {tx_hash_hex} (Block: {receipt.blockNumber})")
                return tx_hash_hex
            else:
                raise Exception(f"Transaction failed: {tx_hash_hex}")
                
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise
    
    async def update_behavioral_data(self, user_address: str, metrics: BehavioralMetrics) -> str:
        """
        Update behavioral data for a user on-chain
        
        Args:
            user_address: User's wallet address
            metrics: Behavioral metrics from DataProcessor
            
        Returns:
            Transaction hash of the update
        """
        try:
            logger.info(f"Updating behavioral data for user: {user_address}")
            
            # Validate user address
            if not self.w3.is_address(user_address):
                raise ValueError(f"Invalid user address: {user_address}")
            
            user_address = self.w3.to_checksum_address(user_address)
            
            # Convert metrics to contract format
            metrics_tuple = self._convert_metrics_to_tuple(metrics)
            
            # Prepare contract function call
            function_call = self.registry_contract.functions.updateBehavioralData(
                user_address,
                metrics_tuple
            )
            
            # Estimate gas
            try:
                gas_estimate = function_call.estimate_gas({'from': self.account.address})
                gas_limit = int(gas_estimate * 120 // 100)  # 20% buffer
                logger.info(f"Estimated gas: {gas_estimate}, using: {gas_limit}")
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}, using default gas limit")
                gas_limit = 300000
            
            # Build and send transaction
            transaction = self._build_transaction(function_call, gas_limit)
            tx_hash = self._send_transaction(transaction)
            
            logger.info(f"Behavioral data updated successfully - TX: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Failed to update behavioral data: {e}")
            raise
    
    async def calculate_credit_score(self, user_address: str) -> str:
        """
        Calculate credit score for a user on-chain
        
        Args:
            user_address: User's wallet address
            
        Returns:
            Transaction hash of the calculation
        """
        try:
            logger.info(f"Calculating credit score for user: {user_address}")
            
            # Validate user address
            if not self.w3.is_address(user_address):
                raise ValueError(f"Invalid user address: {user_address}")
            
            user_address = self.w3.to_checksum_address(user_address)
            
            # Prepare contract function call
            function_call = self.registry_contract.functions.calculateCreditScore(user_address)
            
            # Estimate gas
            try:
                gas_estimate = function_call.estimate_gas({'from': self.account.address})
                gas_limit = int(gas_estimate * 120 // 100)  # 20% buffer
                logger.info(f"Estimated gas: {gas_estimate}, using: {gas_limit}")
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}, using default gas limit")
                gas_limit = 500000
            
            # Build and send transaction
            transaction = self._build_transaction(function_call, gas_limit)
            tx_hash = self._send_transaction(transaction)
            
            logger.info(f"Credit score calculated successfully - TX: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Failed to calculate credit score: {e}")
            raise
    
    async def get_credit_score(self, user_address: str) -> CreditScore:
        """
        Get credit score for a user from contract
        
        Args:
            user_address: User's wallet address
            
        Returns:
            Credit score data
        """
        try:
            # Validate user address
            if not self.w3.is_address(user_address):
                raise ValueError(f"Invalid user address: {user_address}")
            
            user_address = self.w3.to_checksum_address(user_address)
            
            # Call contract
            score_data = self.registry_contract.functions.getCreditScore(user_address).call()
            
            # Convert to CreditScore object
            credit_score = CreditScore(
                totalScore=score_data[0],
                transactionScore=score_data[1],
                defiScore=score_data[2],
                stakingScore=score_data[3],
                riskScore=score_data[4],
                historyScore=score_data[5],
                lastUpdated=score_data[6],
                confidence=score_data[7],
                updateCount=score_data[8],
                isActive=score_data[9]
            )
            
            logger.info(f"Retrieved credit score for {user_address}: {credit_score.totalScore}")
            return credit_score
            
        except Exception as e:
            logger.error(f"Failed to get credit score: {e}")
            raise
    
    async def preview_score(self, metrics: BehavioralMetrics) -> Tuple[int, int]:
        """
        Preview credit score calculation without executing transaction
        
        Args:
            metrics: Behavioral metrics
            
        Returns:
            Tuple of (estimated_score, confidence)
        """
        try:
            # Convert metrics to contract format
            metrics_tuple = self._convert_metrics_to_tuple(metrics)
            
            # Call preview function
            result = self.registry_contract.functions.previewScore(metrics_tuple).call()
            
            estimated_score, confidence = result
            logger.info(f"Score preview: {estimated_score} (confidence: {confidence}%)")
            
            return estimated_score, confidence
            
        except Exception as e:
            logger.error(f"Failed to preview score: {e}")
            raise
    
    async def get_score_history(self, user_address: str) -> List[int]:
        """
        Get score history for a user
        
        Args:
            user_address: User's wallet address
            
        Returns:
            List of historical scores
        """
        try:
            # Validate user address
            if not self.w3.is_address(user_address):
                raise ValueError(f"Invalid user address: {user_address}")
            
            user_address = self.w3.to_checksum_address(user_address)
            
            # Call contract
            history = self.registry_contract.functions.getScoreHistory(user_address).call()
            
            logger.info(f"Retrieved score history for {user_address}: {len(history)} entries")
            return list(history)
            
        except Exception as e:
            logger.error(f"Failed to get score history: {e}")
            raise
    
    async def process_user_complete_flow(self, user_address: str, metrics: BehavioralMetrics) -> Dict[str, Any]:
        """
        Complete flow: Update behavioral data and calculate credit score
        
        Args:
            user_address: User's wallet address
            metrics: Behavioral metrics from DataProcessor
            
        Returns:
            Complete result with transaction hashes and score data
        """
        try:
            logger.info(f"Starting complete flow for user: {user_address}")
            
            # Step 1: Update behavioral data
            update_tx = await self.update_behavioral_data(user_address, metrics)
            
            # Wait a bit for the transaction to be mined
            await asyncio.sleep(5)
            
            # Step 2: Calculate credit score
            calc_tx = await self.calculate_credit_score(user_address)
            
            # Wait for calculation to complete
            await asyncio.sleep(5)
            
            # Step 3: Retrieve calculated score
            credit_score = await self.get_credit_score(user_address)
            
            result = {
                'user_address': user_address,
                'update_transaction': update_tx,
                'calculation_transaction': calc_tx,
                'credit_score': {
                    'total_score': credit_score.totalScore,
                    'transaction_score': credit_score.transactionScore,
                    'defi_score': credit_score.defiScore,
                    'staking_score': credit_score.stakingScore,
                    'risk_score': credit_score.riskScore,
                    'history_score': credit_score.historyScore,
                    'confidence': credit_score.confidence,
                    'last_updated': credit_score.lastUpdated,
                    'is_active': credit_score.isActive
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Complete flow finished successfully for {user_address}")
            logger.info(f"Final score: {credit_score.totalScore} (confidence: {credit_score.confidence}%)")
            
            return result
            
        except Exception as e:
            logger.error(f"Complete flow failed for {user_address}: {e}")
            raise
    
    def get_contract_info(self) -> Dict[str, Any]:
        """Get contract information for debugging"""
        try:
            protocol_version = self.registry_contract.functions.PROTOCOL_VERSION().call()
            owner = self.registry_contract.functions.owner().call()
            is_authorized = self.registry_contract.functions.authorizedDataProviders(self.account.address).call()
            
            return {
                'contract_address': self.registry_address,
                'protocol_version': protocol_version,
                'owner': owner,
                'data_provider_authorized': is_authorized,
                'account_address': self.account.address,
                'chain_id': self.chain_id,
                'rpc_url': self.rpc_url
            }
        except Exception as e:
            logger.error(f"Failed to get contract info: {e}")
            return {'error': str(e)}

# Utility function to create BehavioralMetrics from DataProcessor output
def convert_dataprocessor_to_metrics(processed_data: Dict[str, Any]) -> BehavioralMetrics:
    """
    Convert DataProcessor output to BehavioralMetrics
    
    Args:
        processed_data: Output from your DataProcessor
        
    Returns:
        BehavioralMetrics object ready for contract interaction
    """
    return BehavioralMetrics(
        transactionFrequency=int(processed_data.get('transactionFrequency', 0)),
        averageTransactionValue=int(processed_data.get('averageTransactionValue', 0)),
        gasEfficiencyScore=int(processed_data.get('gasEfficiencyScore', 0)),
        crossChainActivityCount=int(processed_data.get('crossChainActivityCount', 0)),
        consistencyMetric=int(processed_data.get('consistencyMetric', 0)),
        protocolInteractionCount=int(processed_data.get('protocolInteractionCount', 0)),
        totalDeFiBalanceUSD=int(processed_data.get('totalDeFiBalanceUSD', 0)),
        liquidityPositionCount=int(processed_data.get('liquidityPositionCount', 0)),
        protocolDiversityScore=int(processed_data.get('protocolDiversityScore', 0)),
        totalStakedUSD=int(processed_data.get('totalStakedUSD', 0)),
        stakingDurationDays=int(processed_data.get('stakingDurationDays', 0)),
        stakingPlatformCount=int(processed_data.get('stakingPlatformCount', 0)),
        rewardClaimFrequency=int(processed_data.get('rewardClaimFrequency', 0)),
        liquidationEventCount=int(processed_data.get('liquidationEventCount', 0)),
        leverageRatio=int(processed_data.get('leverageRatio', 100)),
        portfolioVolatility=int(processed_data.get('portfolioVolatility', 25)),
        stakingLoyaltyScore=int(processed_data.get('stakingLoyaltyScore', 50)),
        interactionDepthScore=int(processed_data.get('interactionDepthScore', 50)),
        yieldFarmingActive=int(processed_data.get('yieldFarmingActive', 0)),
        accountAgeScore=int(processed_data.get('accountAgeScore', 50)),
        activityConsistencyScore=int(processed_data.get('activityConsistencyScore', 50)),
        engagementScore=int(processed_data.get('engagementScore', 50))
    )
