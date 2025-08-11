import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react';

interface AIAnalysisCardProps {
  analysis: {
    rating: string;
    risk_level: string;
    score: number;
    recommendation: string;
    summary: string;
  };
  delay?: number;
}

const AIAnalysisCard: React.FC<AIAnalysisCardProps> = ({ analysis, delay = 0 }) => {
  const getRatingColor = (rating: string) => {
    switch (rating.toLowerCase()) {
      case 'excellent':
        return 'bg-green-500/20 text-green-600 border-green-500/30';
      case 'good':
        return 'bg-blue-500/20 text-blue-600 border-blue-500/30';
      case 'fair':
        return 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30';
      case 'poor':
        return 'bg-red-500/20 text-red-600 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-600 border-gray-500/30';
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'very_low':
        return 'bg-green-500/20 text-green-600 border-green-500/30';
      case 'low':
        return 'bg-blue-500/20 text-blue-600 border-blue-500/30';
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30';
      case 'high':
        return 'bg-orange-500/20 text-orange-600 border-orange-500/30';
      case 'very_high':
        return 'bg-red-500/20 text-red-600 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-600 border-gray-500/30';
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation.toLowerCase()) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'declined':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'pending':
        return <Info className="w-5 h-5 text-blue-600" />;
      default:
        return <Info className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <Card 
      className="glass p-6 hover:scale-105 transition-transform duration-300 animate-slide-in-up opacity-0 border-border/20"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-gradient-primary rounded-full flex items-center justify-center">
          <Brain className="w-5 h-5 text-primary-foreground" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-card-foreground">AI Analysis</h3>
          <p className="text-sm text-muted-foreground">Powered by Gemini AI</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Rating and Risk Level */}
        <div className="flex flex-wrap gap-3">
          <Badge className={`${getRatingColor(analysis.rating)} border`}>
            Rating: {analysis.rating}
          </Badge>
          <Badge className={`${getRiskLevelColor(analysis.risk_level)} border`}>
            Risk: {analysis.risk_level.replace('_', ' ')}
          </Badge>
        </div>

        {/* Recommendation */}
        <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
          {getRecommendationIcon(analysis.recommendation)}
          <span className="font-medium text-card-foreground">
            Recommendation: {analysis.recommendation}
          </span>
        </div>

        {/* Summary */}
        <div className="space-y-2">
          <h4 className="font-medium text-card-foreground flex items-center gap-2">
            <Info className="w-4 h-4 text-primary" />
            Analysis Summary
          </h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {analysis.summary}
          </p>
        </div>

        {/* Score */}
        <div className="flex items-center justify-between p-3 bg-gradient-primary/10 rounded-lg border border-primary/20">
          <span className="text-sm font-medium text-card-foreground">AI Score</span>
          <span className="text-lg font-bold gradient-text">{analysis.score}</span>
        </div>
      </div>
    </Card>
  );
};

export default AIAnalysisCard; 