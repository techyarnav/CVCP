import React from 'react';
import { Card } from '@/components/ui/card';

interface ScoreCardProps {
  title: string;
  score: number;
  maxScore?: number;
  weight?: number;
  icon: React.ReactNode;
  delay?: number;
  showPercentage?: boolean;
}

const ScoreCard: React.FC<ScoreCardProps> = ({ 
  title, 
  score, 
  maxScore = 200, 
  weight, 
  icon, 
  delay = 0,
  showPercentage = true
}) => {
  const percentage = maxScore ? (score / maxScore) * 100 : 0;

  return (
    <Card 
      className="glass p-6 hover:scale-105 transition-transform duration-300 animate-slide-in-up opacity-0 border-border/20"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-primary text-xl">
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-card-foreground">{title}</h3>
            {weight && <p className="text-sm text-muted-foreground">{weight}% weight</p>}
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold gradient-text animate-count-up">
            {score}
          </div>
          {maxScore && <div className="text-sm text-muted-foreground">/ {maxScore}</div>}
        </div>
      </div>
      
      {showPercentage && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="text-card-foreground font-medium">{Math.round(percentage)}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
            <div 
              className="h-full bg-gradient-primary transition-all duration-1000 ease-out rounded-full"
              style={{ 
                width: `${percentage}%`,
                animationDelay: `${delay + 0.5}s`
              }}
            />
          </div>
        </div>
      )}
    </Card>
  );
};

export default ScoreCard;