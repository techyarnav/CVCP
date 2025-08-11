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
    description="On-chain credit scoring protocol API with AI analysis and smart rate limiting",
    version="1.1.0",
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

# ✅ Initialize Gemini AI Service (Import from your separate file)
try:
    from services.gemini_ai_service import GeminiAIService
    gemini_ai = GeminiAIService()
    logger.info("✅ Gemini AI service initialized successfully")
except Exception as e:
    gemini_ai = None
    logger.warning(f"⚠️ Gemini AI initialization failed: {e}")

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

# In your existing API file, just change this one class:

class ScoreCalculationResponse(BaseModel):
    success: bool
    address: str
    credit_score: Optional[Dict[str, Any]] = None
    contract_transactions: Optional[Dict[str, str]] = None
    processing_time_seconds: Optional[float] = None
    ai_analysis: Optional[Dict[str, Any]] = None  # ✅ Changed from str to Dict[str, Any]
    rate_limited: Optional[bool] = False
    cache_used: Optional[bool] = False
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

# ✅ Helper function to check contract rate limiting
async def check_contract_cooldown(address: str) -> Dict[str, Any]:
    """Check if address is in contract cooldown period"""
    try:
        from services.contract_bridge import ContractBridge
        contract_bridge = ContractBridge()
        
        existing_score = await contract_bridge.get_credit_score(address)
        
        if existing_score and existing_score.isActive:
            current_time = int(time.time())
            last_updated = existing_score.lastUpdated
            time_diff = current_time - last_updated
            cooldown_period = 1800  # 30 minutes in seconds
            
            if time_diff < cooldown_period:
                remaining_time = cooldown_period - time_diff
                return {
                    'in_cooldown': True,
                    'existing_score': existing_score,
                    'time_diff_minutes': time_diff // 60,
                    'remaining_minutes': remaining_time // 60,
                    'can_use_cache': True
                }
        
        return {'in_cooldown': False, 'existing_score': existing_score}
        
    except Exception as e:
        logger.error(f"Error checking cooldown for {address}: {e}")
        return {'in_cooldown': False, 'existing_score': None}

# API Routes

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Crypto Credit Score Protocol API with AI Analysis & Smart Rate Limiting",
        "version": "1.1.0",
        "status": "operational",
        "docs": "/docs",
        "contract": config.CONTRACT_ADDRESS,
        "ai_enabled": bool(gemini_ai),
        "rate_limiting": {
            "api_requests_per_minute": config.RATE_LIMIT_PER_MINUTE,
            "contract_cooldown_minutes": 30,
            "cache_duration_minutes": 30
        }
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
        contract_status = "connected" if contract_info.get('success', False) else "disconnected"
    except Exception as e:
        contract_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "data_processor": "operational",
            "contract_bridge": contract_status,
            "gemini_ai": "operational" if gemini_ai else "disabled",
            "rate_limiting": "active",
            "api": "operational"
        }
    }

@app.post("/api/calculate-score", response_model=ScoreCalculationResponse)
async def calculate_credit_score(
    request: CalculateScoreRequest,
    background_tasks: BackgroundTasks
):
    """
    Calculate credit score for a wallet address with smart rate limiting and AI analysis
    
    This endpoint:
    1. Checks API rate limiting
    2. Checks contract cooldown period
    3. Returns cached score if in cooldown (unless force_refresh=true)
    4. Processes on-chain behavioral data
    5. Updates smart contract with behavioral metrics
    6. Triggers score calculation on-chain
    7. Generates AI analysis of the credit score
    8. Returns the calculated credit score with AI insights
    """
    
    start_time = time.time()
    
    try:
        # Step 1: API Rate limiting
        if not rate_limit_check(request.address):
            raise HTTPException(
                status_code=429,
                detail="API rate limit exceeded. Please try again later."
            )
        
        logger.info(f"Starting credit score calculation for {request.address}")
        
        # Step 2: Check contract cooldown period
        cooldown_info = await check_contract_cooldown(request.address)
        
        if cooldown_info['in_cooldown'] and not request.force_refresh:
            logger.info(f"⏰ Address {request.address} in cooldown period - returning cached score")
            
            existing_score = cooldown_info['existing_score']
            
            # Generate AI analysis for cached score
            ai_analysis = None
            if gemini_ai and existing_score:
                try:
                    logger.info("Generating AI analysis for cached score...")
                    score_data = {
                        'total_score': existing_score.totalScore,
                        'transaction_score': existing_score.transactionScore,
                        'defi_score': existing_score.defiScore,
                        'staking_score': existing_score.stakingScore,
                        'risk_score': existing_score.riskScore,
                        'history_score': existing_score.historyScore
                    }
                    ai_analysis = await gemini_ai.analyze_credit_score(score_data)
                    logger.info("✅ AI analysis completed for cached score")
                except Exception as ai_error:
                    logger.error(f"AI analysis failed for cached score: {ai_error}")
                    ai_analysis = "AI analysis temporarily unavailable"
            
            processing_time = time.time() - start_time
            
            return ScoreCalculationResponse(
                success=True,
                address=request.address,
                credit_score={
                    'totalScore': existing_score.totalScore,
                    'transactionScore': existing_score.transactionScore,
                    'defiScore': existing_score.defiScore,
                    'stakingScore': existing_score.stakingScore,
                    'riskScore': existing_score.riskScore,
                    'historyScore': existing_score.historyScore,
                    'confidence': existing_score.confidence,
                    'lastUpdated': existing_score.lastUpdated,
                    'updateCount': existing_score.updateCount,
                    'isActive': existing_score.isActive
                } if existing_score else None,
                contract_transactions={},
                processing_time_seconds=round(processing_time, 2),
                ai_analysis=ai_analysis,
                rate_limited=True,
                cache_used=True,
                error=None,
                timestamp=datetime.now().isoformat()
            )
        
        # Step 3: Proceed with full calculation (either no cooldown or force_refresh=true)
        if cooldown_info['in_cooldown'] and request.force_refresh:
            logger.info(f"🔄 Force refresh requested for {request.address} - bypassing cooldown")
        
        logger.info("Step 1: Processing behavioral data...")
        
        # Import fresh to avoid caching issues
        from services.data_processor import DataProcessor
        from services.contract_bridge import ContractBridge
        
        # Initialize fresh components
        data_processor_fresh = DataProcessor()
        contract_bridge_fresh = ContractBridge()
        
        contract_metrics, processing_metadata = await data_processor_fresh.process_user_behavioral_data(
            request.address
        )
        
        if processing_metadata.get('processing_status') != 'success':
            logger.warning(f"Data processing issues: {processing_metadata}")
        
        # Step 4: Execute complete contract flow with enhanced error handling
        logger.info("Step 2: Executing contract interactions...")
        try:
            contract_result = await contract_bridge_fresh.full_score_calculation_flow(
                request.address, 
                contract_metrics
            )
        except Exception as contract_error:
            error_msg = str(contract_error)
            
            # Handle specific errors
            if "Update too frequent" in error_msg:
                logger.warning(f"⏰ Contract rate limit hit for {request.address}")
                
                # Try to return existing score with explanation
                try:
                    existing_score = await contract_bridge_fresh.get_credit_score(request.address)
                    if existing_score and existing_score.isActive:
                        # Generate AI analysis for existing score
                        ai_analysis = None
                        if gemini_ai:
                            score_data = {
                                'total_score': existing_score.totalScore,
                                'transaction_score': existing_score.transactionScore,
                                'defi_score': existing_score.defiScore,
                                'staking_score': existing_score.stakingScore,
                                'risk_score': existing_score.riskScore,
                                'history_score': existing_score.historyScore
                            }
                            ai_analysis = await gemini_ai.analyze_credit_score(score_data)
                        
                        processing_time = time.time() - start_time
                        
                        return ScoreCalculationResponse(
                            success=True,
                            address=request.address,
                            credit_score={
                                'totalScore': existing_score.totalScore,
                                'transactionScore': existing_score.transactionScore,
                                'defiScore': existing_score.defiScore,
                                'stakingScore': existing_score.stakingScore,
                                'riskScore': existing_score.riskScore,
                                'historyScore': existing_score.historyScore,
                                'confidence': existing_score.confidence,
                                'lastUpdated': existing_score.lastUpdated,
                                'updateCount': existing_score.updateCount,
                                'isActive': existing_score.isActive
                            },
                            contract_transactions={},
                            processing_time_seconds=round(processing_time, 2),
                            ai_analysis=ai_analysis,
                            rate_limited=True,
                            cache_used=True,
                            error="Contract update rate limited - returned cached score. Please wait 30 minutes between updates.",
                            timestamp=datetime.now().isoformat()
                        )
                except:
                    pass
                
                raise HTTPException(
                    status_code=429,
                    detail="Contract rate limited: Please wait at least 30 minutes between score updates for the same address."
                )
            
            elif "Unauthorized provider" in error_msg:
                logger.error(f"Contract authorization error: {error_msg}")
                raise HTTPException(
                    status_code=403,
                    detail="Contract authorization error: The configured account is not authorized as a data provider. Please contact administrator."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Contract interaction failed: {error_msg}"
                )
        
        if not contract_result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=f"Contract interaction failed: {contract_result.get('error', 'Unknown error')}"
            )
        
        # Step 5: Generate AI Analysis for new score
        ai_analysis = None
        if gemini_ai and contract_result.get('credit_score'):
            try:
                logger.info("Step 3: Generating AI analysis...")
                credit_score_data = contract_result['credit_score']
                
                score_data = {
                    'total_score': credit_score_data.get('totalScore', 0),
                    'transaction_score': credit_score_data.get('transactionScore', 0),
                    'defi_score': credit_score_data.get('defiScore', 0),
                    'staking_score': credit_score_data.get('stakingScore', 0),
                    'risk_score': credit_score_data.get('riskScore', 0),
                    'history_score': credit_score_data.get('historyScore', 0)
                }
                
                ai_analysis = await gemini_ai.analyze_credit_score(score_data)
                logger.info("✅ AI analysis completed successfully")
                
            except Exception as ai_error:
                logger.error(f"AI analysis failed: {ai_error}")
                ai_analysis = "AI analysis temporarily unavailable"
        
        processing_time = time.time() - start_time
        
        logger.info(f"Credit score calculation completed for {request.address} in {processing_time:.2f}s")
        
        return ScoreCalculationResponse(
            success=True,
            address=request.address,
            credit_score=contract_result.get('credit_score'),
            contract_transactions=contract_result.get('transactions'),
            processing_time_seconds=round(processing_time, 2),
            ai_analysis=ai_analysis,
            rate_limited=False,
            cache_used=False,
            error=None,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        logger.error(f"Error calculating credit score for {request.address}: {str(e)}")
        
        return ScoreCalculationResponse(
            success=False,
            address=request.address,
            credit_score=None,
            contract_transactions=None,
            processing_time_seconds=round(processing_time, 2),
            ai_analysis=None,
            rate_limited=False,
            cache_used=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

@app.get("/api/score/{address}", response_model=CreditScoreResponse)
async def get_credit_score(address: str):
    """Get existing credit score for a wallet address"""
    
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
        credit_score = await contract_bridge_local.get_credit_score(address)
        
        # Handle CreditScore object properly
        if not credit_score or not credit_score.isActive:
            raise HTTPException(
                status_code=404,
                detail=f"No active credit score found for address {address}. Use /api/calculate-score to generate one."
            )
        
        return CreditScoreResponse(
            success=True,
            address=address,
            credit_score={
                'totalScore': credit_score.totalScore,
                'transactionScore': credit_score.transactionScore,
                'defiScore': credit_score.defiScore,
                'stakingScore': credit_score.stakingScore,
                'riskScore': credit_score.riskScore,
                'historyScore': credit_score.historyScore,
                'lastUpdated': credit_score.lastUpdated,
                'confidence': credit_score.confidence,
                'updateCount': credit_score.updateCount,
                'isActive': credit_score.isActive
            },
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
    """Preview what the credit score calculation would be without executing on-chain"""
    
    try:
        # Validate address
        if not address or len(address) != 42 or not address.startswith('0x'):
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address format"
            )
        
        address = address.lower()
        logger.info(f"Generating score preview for {address}")
        
        # Import fresh to avoid caching issues
        from services.data_processor import DataProcessor
        data_processor_local = DataProcessor()
        
        # Use the preview method that exists in DataProcessor
        preview = await data_processor_local.preview_contract_data(address)
        
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

# ✅ New endpoint to get AI analysis for existing scores
@app.get("/api/analyze/{address}")
async def analyze_existing_score(address: str):
    """Get AI analysis for an existing credit score using your separate AI service"""
    
    try:
        # Validate address
        if not address or len(address) != 42 or not address.startswith('0x'):
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address format"
            )
        
        address = address.lower()
        
        if not gemini_ai:
            raise HTTPException(
                status_code=503,
                detail="AI analysis service is not available"
            )
        
        # Get existing credit score
        from services.contract_bridge import ContractBridge
        contract_bridge = ContractBridge()
        credit_score = await contract_bridge.get_credit_score(address)
        
        if not credit_score or not credit_score.isActive:
            raise HTTPException(
                status_code=404,
                detail="No active credit score found for this address"
            )
        
        # Generate AI analysis using your separate service
        score_data = {
            'total_score': credit_score.totalScore,
            'transaction_score': credit_score.transactionScore,
            'defi_score': credit_score.defiScore,
            'staking_score': credit_score.stakingScore,
            'risk_score': credit_score.riskScore,
            'history_score': credit_score.historyScore
        }
        
        ai_analysis = await gemini_ai.analyze_credit_score(score_data)
        
        return {
            "success": True,
            "address": address,
            "credit_score": credit_score.totalScore,
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing score for {address}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ✅ New endpoint to check rate limit status
@app.get("/api/rate-limit-status/{address}")
async def get_rate_limit_status(address: str):
    """Check rate limit status for an address"""
    
    try:
        if not address or len(address) != 42 or not address.startswith('0x'):
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address format"
            )
        
        address = address.lower()
        
        # Check contract cooldown
        cooldown_info = await check_contract_cooldown(address)
        
        return {
            "success": True,
            "address": address,
            "contract_cooldown": {
                "in_cooldown": cooldown_info['in_cooldown'],
                "minutes_since_last_update": cooldown_info.get('time_diff_minutes', 0),
                "minutes_remaining": cooldown_info.get('remaining_minutes', 0),
                "can_update": not cooldown_info['in_cooldown']
            },
            "has_existing_score": bool(cooldown_info.get('existing_score')),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
        "rate_limit_per_minute": config.RATE_LIMIT_PER_MINUTE,
        "contract_cooldown_minutes": 30,
        "ai_enabled": bool(gemini_ai)
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
            "chain_id": getattr(config, 'CHAIN_ID', 534351),
            "ai_enabled": bool(gemini_ai),
            "rate_limiting": {
                "contract_cooldown_minutes": 30,
                "api_requests_per_minute": config.RATE_LIMIT_PER_MINUTE
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "contract_address": config.CONTRACT_ADDRESS,
            "chain_id": getattr(config, 'CHAIN_ID', 534351)
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
        logger.info("🚀 Credit Score API with Smart Rate Limiting & AI Analysis started successfully")
        logger.info(f"📄 Contract: {config.CONTRACT_ADDRESS}")
        logger.info(f"🌐 Server: http://{config.API_HOST}:{config.API_PORT}")
        logger.info(f"🤖 AI Analysis: {'✅ Enabled' if gemini_ai else '❌ Disabled'}")
        logger.info(f"⏰ Rate Limiting: API={config.RATE_LIMIT_PER_MINUTE}/min, Contract=30min cooldown")
        
        # Test contract connection with fresh import
        try:
            from services.contract_bridge import ContractBridge
            contract_bridge_local = ContractBridge()
            contract_info = contract_bridge_local.get_contract_info()
            logger.info(f"✅ Contract connection successful: {contract_info}")
        except Exception as e:
            logger.warning(f"⚠️ Contract connection issue (will continue): {e}")
            
    except Exception as e:
        logger.error(f"❌ Failed to start API: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run(
        "credit_score_api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_DEBUG,
        log_level="info"
    )
