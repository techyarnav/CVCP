# backend/services/gemini-ai-service.py

import google.generativeai as genai
import os
import json
from typing import Dict, Any
from loguru import logger

class GeminiAIService:
    def __init__(self):
        # Use Gemini-1.0-Pro model (free tier)
        api_key = "<YOUR_GEMINI_API_KEY>"
        if not api_key:
            raise ValueError("GEMINI_AI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        # Updated to use the correct model name
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def analyze_credit_score(self, score_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze credit score data and provide AI-enhanced insights in simple JSON format"""
        try:
            prompt = self._generate_analysis_prompt(score_data)
            response = self.model.generate_content(prompt)
            
            # Convert text response to simple JSON structure
            return self._convert_to_simple_json(response.text, score_data)
            
        except Exception as e:
            logger.error(f"Gemini AI analysis failed: {str(e)}")
            return self._get_fallback_analysis(score_data)

    def _generate_analysis_prompt(self, score_data: Dict[str, Any]) -> str:
        return f"""
        Analyze this DeFi credit profile as a financial expert. Include risk assessment:

        Credit Score: {score_data['total_score']} (Range: 300-850)
        Components:
        - Transaction Score: {score_data['transaction_score']}/100
        - DeFi Score: {score_data['defi_score']}/100
        - Staking Score: {score_data['staking_score']}/100
        - Risk Score: {score_data['risk_score']}/100
        - History Score: {score_data['history_score']}/100

        Provide a brief analysis including risk level and lending suitability.
        """

    def _convert_to_simple_json(self, ai_text: str, score_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AI text to simple JSON with 5 key-value pairs"""
        
        total_score = score_data['total_score']
        risk_score = score_data['risk_score']
        
        # Determine simple ratings
        if total_score >= 750:
            rating = "excellent"
            risk_level = "low"
        elif total_score >= 670:
            rating = "good"
            risk_level = "moderate"
        elif total_score >= 580:
            rating = "fair"
            risk_level = "moderate"
        else:
            rating = "poor"
            risk_level = "high"
        
        # Override risk level if risk score is very high
        if risk_score > 100:
            risk_level = "very_high"
        elif risk_score > 80:
            risk_level = "high"
        
        return {
            "rating": rating,
            "risk_level": risk_level,
            "score": total_score,
            "recommendation": "approved" if rating in ["excellent", "good"] else "conditional" if rating == "fair" else "declined",
            "summary": ai_text[:200] + "..." if len(ai_text) > 200 else ai_text
        }

    def _get_fallback_analysis(self, score_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return fallback analysis as JSON object"""
        
        total_score = score_data['total_score']
        risk_score = score_data['risk_score']
        
        if risk_score > 100:
            risk_level = "very_high"
        elif risk_score >= 80:
            risk_level = "high"
        elif risk_score >= 60:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        if total_score >= 750:
            rating = "excellent"
            recommendation = "approved"
            summary = f"Excellent credit profile with {risk_level} risk for DeFi lending."
        elif total_score >= 670:
            rating = "good"
            recommendation = "approved"
            summary = f"Good credit profile with {risk_level} risk for DeFi lending."
        elif total_score >= 580:
            rating = "fair"
            recommendation = "conditional"
            summary = f"Fair credit profile with {risk_level} risk - careful evaluation needed."
        else:
            rating = "poor"
            recommendation = "declined"
            summary = f"Limited credit profile with {risk_level} risk - high caution advised."
        
        return {
            "rating": rating,
            "risk_level": risk_level,
            "score": total_score,
            "recommendation": recommendation,
            "summary": summary
        }
