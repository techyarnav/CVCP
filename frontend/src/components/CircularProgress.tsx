import React, { useEffect, useState } from 'react';

interface CircularProgressProps {
  score: number;
  maxScore?: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

const CircularProgress: React.FC<CircularProgressProps> = ({
  score,
  maxScore = 850,
  size = 200,
  strokeWidth = 8,
  className = ""
}) => {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const percentage = (animatedScore / maxScore) * 100;
  const offset = circumference - (percentage / 100) * circumference;

  // Score range colors
  const getScoreColor = (currentScore: number) => {
    if (currentScore >= 750) return 'hsl(var(--secondary))'; // Excellent - Green
    if (currentScore >= 650) return 'hsl(var(--primary))'; // Good - Blue
    if (currentScore >= 550) return 'hsl(var(--accent))'; // Fair - Purple
    return 'hsl(var(--destructive))'; // Poor - Red
  };

  const getScoreLabel = (currentScore: number) => {
    if (currentScore >= 750) return 'Excellent';
    if (currentScore >= 650) return 'Good';
    if (currentScore >= 550) return 'Fair';
    return 'Poor';
  };

  useEffect(() => {
    setIsVisible(true);
    
    // Animate score counting up
    const animationDuration = 2000;
    const steps = 50;
    const stepValue = score / steps;
    const stepDelay = animationDuration / steps;

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      const newScore = Math.min(stepValue * currentStep, score);
      setAnimatedScore(newScore);

      if (currentStep >= steps) {
        clearInterval(timer);
      }
    }, stepDelay);

    return () => clearInterval(timer);
  }, [score]);

  return (
    <div className={`relative ${className}`}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
        viewBox={`0 0 ${size} ${size}`}
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="hsl(var(--muted))"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="opacity-20"
        />
        
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getScoreColor(animatedScore)}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500 ease-out"
          style={{
            filter: `drop-shadow(0 0 8px ${getScoreColor(animatedScore)}40)`
          }}
        />
      </svg>
      
      {/* Score display */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div 
            className={`text-5xl font-bold gradient-text transition-opacity duration-1000 ${
              isVisible ? 'opacity-100' : 'opacity-0'
            }`}
          >
            {Math.round(animatedScore)}
          </div>
          <div className="text-sm text-muted-foreground mt-1">
            / {maxScore}
          </div>
          <div 
            className={`text-lg font-semibold mt-2 transition-opacity duration-1000 delay-500 ${
              isVisible ? 'opacity-100' : 'opacity-0'
            }`}
            style={{ color: getScoreColor(animatedScore) }}
          >
            {getScoreLabel(animatedScore)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CircularProgress;