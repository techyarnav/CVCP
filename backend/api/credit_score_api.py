# backend/api/credit_score_api.py

import asyncio
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from loguru import logger
import uvicorn

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="Crypto Credit Score API",
    description="On-chain credit scoring protocol API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize only config globally 
config = Config()

# Request/Response Models
class CalculateScoreRequest(BaseModel):
    address: str
    force_refresh: Optional[bool] = False
    
    @validator('address')
    def validate_address(cls, v):
        if not v or len(v) != 42 or not v.startswith('0x'):
            raise ValueError('Invalid Ethereum address format')
        return v.lower()

class CreditScoreResponse(BaseModel):
    success: bool
    address: str
    credit_score: Optional[Dict[str, Any]] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class ScoreCalculationResponse(BaseModel):
    success: bool
    address: str
    credit_score: Optional[Dict[str, Any]] = None
    contract_transactions: Optional[Dict[str, str]] = None
    processing_time_seconds: Optional[float] = None
    error: Optional[str] = None
    timestamp: str

# Rate limiting (simple in-memory implementation)
request_history = {}

def rate_limit_check(address: str) -> bool:
    """Simple rate limiting check"""
    now = time.time()
    if address not in request_history:
        request_history[address] = []
    
    # Clean old requests (older than 1 minute)
    request_history[address] = [
        req_time for req_time in request_history[address] 
        if now - req_time < 60
    ]
    
    # Check rate limit
    if len(request_history[address]) >= config.RATE_LIMIT_PER_MINUTE:
        return False
    
    request_history[address].append(now)
    return True

# API Routes

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Crypto Credit Score Protocol API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "contract": config.CONTRACT_ADDRESS
    }

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    try:
        # Import fresh to avoid caching issues
        from services.contract_bridge import ContractBridge
        contract_bridge_local = ContractBridge()
        
        # Check contract connection
        contract_info = contract_bridge_local.get_contract_info()
        contract_status = "connected" if contract_info else "disconnected"
    except Exception as e:
        contract_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "data_processor": "operational",
            "contract_bridge": contract_status,
            "api": "operational"
        }
    }

@app.post("/api/calculate-score", response_model=ScoreCalculationResponse)
async def calculate_credit_score(
    request: CalculateScoreRequest,
    background_tasks: BackgroundTasks
):
    """
    Calculate credit score for a wallet address
    
    This endpoint:
    1. Processes on-chain behavioral data
    2. Updates smart contract with behavioral metrics
    3. Triggers score calculation on-chain
    4. Returns the calculated credit score
    """
    
    start_time = time.time()
    
    try:
        # Rate limiting
        if not rate_limit_check(request.address):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        logger.info(f"Starting credit score calculation for {request.address}")
        
        # Step 1: Process behavioral data
        logger.info("Step 1: Processing behavioral data...")
        
        # Import fresh to avoid caching issues
        from services.data_processor import DataProcessor
        from services.contract_bridge import ContractBridge, BehavioralMetrics
        
        # Initialize fresh components
        data_processor_fresh = DataProcessor()
        contract_bridge_fresh = ContractBridge()
        
        contract_metrics, processing_metadata = await data_processor_fresh.process_user_behavioral_data(
            request.address
        )
        
        if processing_metadata.get('processing_status') != 'success':
            logger.warning(f"Data processing issues: {processing_metadata}")
        
        # Step 2: Convert to behavioral metrics format expected by contract bridge
        logger.info("Step 2: Converting to behavioral metrics format...")
        
        # Create BehavioralMetrics dataclass object
        behavioral_metrics = BehavioralMetrics(
            transactionFrequency=contract_metrics.get('transactionFrequency', 0),
            averageTransactionValue=contract_metrics.get('averageTransactionValue', 0),
            gasEfficiencyScore=contract_metrics.get('gasEfficiencyScore', 50),
            crossChainActivityCount=contract_metrics.get('crossChainActivityCount', 0),
            consistencyMetric=contract_metrics.get('consistencyMetric', 0),
            protocolInteractionCount=contract_metrics.get('protocolInteractionCount', 0),
            totalDeFiBalanceUSD=contract_metrics.get('totalDeFiBalanceUSD', 0),
            liquidityPositionCount=contract_metrics.get('liquidityPositionCount', 0),
            protocolDiversityScore=contract_metrics.get('protocolDiversityScore', 0),
            interactionDepthScore=contract_metrics.get('interactionDepthScore', 0),
            yieldFarmingActive=contract_metrics.get('yieldFarmingActive', 0),
            totalStakedUSD=contract_metrics.get('totalStakedUSD', 0),
            stakingDurationDays=contract_metrics.get('stakingDurationDays', 0),
            stakingPlatformCount=contract_metrics.get('stakingPlatformCount', 0),
            rewardClaimFrequency=contract_metrics.get('rewardClaimFrequency', 0),
            stakingLoyaltyScore=contract_metrics.get('stakingLoyaltyScore', 0),
            liquidationEventCount=contract_metrics.get('liquidationEventCount', 0),
            leverageRatio=contract_metrics.get('leverageRatio', 100),
            portfolioVolatility=contract_metrics.get('portfolioVolatility', 50),
            accountAgeScore=contract_metrics.get('accountAgeScore', 50),
            activityConsistencyScore=contract_metrics.get('activityConsistencyScore', 33),
            engagementScore=contract_metrics.get('engagementScore', 50)
        )
        
        # Step 3: Execute complete contract flow
        logger.info("Step 3: Executing contract interactions...")
        try:
            # Use the fresh contract bridge
            contract_result = await contract_bridge_fresh.process_user_complete_flow(
                request.address, 
                behavioral_metrics
            )
        except Exception as contract_error:
            error_msg = str(contract_error)
            
            # Handle specific authorization error
            if "Unauthorized provider" in error_msg:
                logger.error(f"Contract authorization error: {error_msg}")
                
                # Try individual operations to better understand the issue
                try:
                    # First, try to get current score (read-only)
                    existing_score = await contract_bridge.get_credit_score(request.address)
                    logger.info(f"Read operation successful: {existing_score}")
                    
                    # The issue is with write operations - account not authorized
                    raise HTTPException(
                        status_code=403,
                        detail="Contract authorization error: The configured account is not authorized as a data provider. Please contact administrator."
                    )
                except Exception as read_error:
                    logger.error(f"Even read operations failing: {read_error}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Contract connection error: {read_error}"
                    )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Contract interaction failed: {error_msg}"
                )
        
        if not contract_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Contract interaction failed: {contract_result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Credit score calculation completed for {request.address} in {processing_time:.2f}s")
        
        return ScoreCalculationResponse(
            success=True,
            address=request.address,
            credit_score=contract_result['credit_score'],
            contract_transactions=contract_result['transactions'],
            processing_time_seconds=round(processing_time, 2),
            error=None,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error calculating credit score for {request.address}: {str(e)}")
        
        return ScoreCalculationResponse(
            success=False,
            address=request.address,
            credit_score=None,
            contract_transactions=None,
            processing_time_seconds=round(processing_time, 2),
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

@app.get("/api/score/{address}", response_model=CreditScoreResponse)
async def get_credit_score(address: str):
    """
    Get existing credit score for a wallet address
    
    Returns the current credit score stored on-chain without triggering recalculation
    """
    
    try:
        # Validate address format
        if not address or len(address) != 42 or not address.startswith('0x'):
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address format"
            )
        
        address = address.lower()
        
        # Rate limiting
        if not rate_limit_check(address):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        logger.info(f"Retrieving credit score for {address}")
        
        # Import fresh to avoid caching issues
        from services.contract_bridge import ContractBridge
        contract_bridge_local = ContractBridge()
        
        # Get score from contract
        result = await contract_bridge_local.get_credit_score(address)
        
        if not result['success']:
            error_msg = result['error']
            if "no score found" in error_msg.lower() or "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=404,
                    detail=f"No credit score found for address {address}. Use /api/calculate-score to generate one."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error retrieving score: {error_msg}"
                )
        
        # Check if score is active
        credit_score = result['credit_score']
        if not credit_score.isActive:
            raise HTTPException(
                status_code=404,
                detail=f"No active credit score found for address {address}"
            )
        
        return CreditScoreResponse(
            success=True,
            address=address,
            credit_score=credit_score.__dict__,
            processing_metadata={
                'source': 'on_chain',
                'last_updated': credit_score.lastUpdated,
                'update_count': credit_score.updateCount
            },
            error=None,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credit score for {address}: {str(e)}")
        
        return CreditScoreResponse(
            success=False,
            address=address,
            credit_score=None,
            processing_metadata=None,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

@app.get("/api/preview/{address}")
async def preview_score_calculation(address: str):
    """
    Preview what the credit score calculation would be without executing on-chain
    
    Useful for testing and showing users what their score would be
    """
    
    try:
        # Validate address
        if not address or len(address) != 42 or not address.startswith('0x'):
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address format"
            )
        
        address = address.lower()
        
        logger.info(f"Generating score preview for {address}")
        
        # Get preview from data processor
        try:
            # Import fresh to avoid caching issues
            from services.data_processor import DataProcessor
            from services.contract_bridge import ContractBridge, BehavioralMetrics
            
            data_processor_local = DataProcessor()
            contract_bridge_local = ContractBridge()
            
            contract_metrics, processing_metadata = await data_processor_local.process_user_behavioral_data(address)
            
            # Create BehavioralMetrics dataclass object
            behavioral_metrics = BehavioralMetrics(
                transactionFrequency=contract_metrics.get('transactionFrequency', 0),
                averageTransactionValue=contract_metrics.get('averageTransactionValue', 0),
                gasEfficiencyScore=contract_metrics.get('gasEfficiencyScore', 50),
                crossChainActivityCount=contract_metrics.get('crossChainActivityCount', 0),
                consistencyMetric=contract_metrics.get('consistencyMetric', 0),
                protocolInteractionCount=contract_metrics.get('protocolInteractionCount', 0),
                totalDeFiBalanceUSD=contract_metrics.get('totalDeFiBalanceUSD', 0),
                liquidityPositionCount=contract_metrics.get('liquidityPositionCount', 0),
                protocolDiversityScore=contract_metrics.get('protocolDiversityScore', 0),
                interactionDepthScore=contract_metrics.get('interactionDepthScore', 0),
                yieldFarmingActive=contract_metrics.get('yieldFarmingActive', 0),
                totalStakedUSD=contract_metrics.get('totalStakedUSD', 0),
                stakingDurationDays=contract_metrics.get('stakingDurationDays', 0),
                stakingPlatformCount=contract_metrics.get('stakingPlatformCount', 0),
                rewardClaimFrequency=contract_metrics.get('rewardClaimFrequency', 0),
                stakingLoyaltyScore=contract_metrics.get('stakingLoyaltyScore', 0),
                liquidationEventCount=contract_metrics.get('liquidationEventCount', 0),
                leverageRatio=contract_metrics.get('leverageRatio', 100),
                portfolioVolatility=contract_metrics.get('portfolioVolatility', 50),
                accountAgeScore=contract_metrics.get('accountAgeScore', 50),
                activityConsistencyScore=contract_metrics.get('activityConsistencyScore', 33),
                engagementScore=contract_metrics.get('engagementScore', 50)
            )
            
            # Get score preview from contract bridge
            score_preview = await contract_bridge_local.preview_score(behavioral_metrics)
            
            return {
                "success": True,
                "address": address,
                "preview": {
                    "predicted_score": score_preview[0] if isinstance(score_preview, tuple) else score_preview.get('score'),
                    "confidence": score_preview[1] if isinstance(score_preview, tuple) else score_preview.get('confidence'),
                    "contract_metrics": contract_metrics,
                    "processing_metadata": processing_metadata
                },
                "note": "This is a preview only. Use /api/calculate-score to execute on-chain."
            }
            
        except Exception as preview_error:
            # Fallback to data processor preview
            preview = await data_processor.preview_contract_data(address)
            
            if 'error' in preview:
                return {
                    "success": False,
                    "error": preview['error'],
                    "fallback_data": preview.get('fallback_data')
                }
            
            return {
                "success": True,
                "address": address,
                "preview": preview,
                "note": "This is a preview only. Use /api/calculate-score to execute on-chain."
            }
        
    except Exception as e:
        logger.error(f"Error generating preview for {address}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/stats")
async def get_api_stats():
    """Get API usage statistics"""
    
    total_requests = sum(len(requests) for requests in request_history.values())
    active_addresses = len([addr for addr, requests in request_history.items() if requests])
    
    return {
        "total_requests_last_hour": total_requests,
        "active_addresses": active_addresses,
        "contract_address": config.CONTRACT_ADDRESS,
        "rate_limit_per_minute": config.RATE_LIMIT_PER_MINUTE
    }

@app.get("/api/contract-info")
async def get_contract_info():
    """Get contract information and status"""
    try:
        # Import fresh to avoid caching issues
        from services.contract_bridge import ContractBridge
        contract_bridge_local = ContractBridge()
        
        contract_info = contract_bridge_local.get_contract_info()
        return {
            "success": True,
            "contract_info": contract_info,
            "contract_address": config.CONTRACT_ADDRESS,
            "chain_id": config.CHAIN_ID
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "contract_address": config.CONTRACT_ADDRESS,
            "chain_id": config.CHAIN_ID
        }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize API on startup"""
    try:
        config.validate()
        logger.info("Credit Score API started successfully")
        logger.info(f"Contract: {config.CONTRACT_ADDRESS}")
        logger.info(f"Server: http://{config.API_HOST}:{config.API_PORT}")
        
        # Test contract connection with fresh import
        try:
            from services.contract_bridge import ContractBridge
            contract_bridge_local = ContractBridge()
            contract_info = contract_bridge_local.get_contract_info()
            logger.info(f"Contract connection successful: {contract_info}")
        except Exception as e:
            logger.warning(f"Contract connection issue (will continue): {e}")
            
    except Exception as e:
        logger.error(f"Failed to start API: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run(
        "credit_score_api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_DEBUG,
        log_level="info"
    )