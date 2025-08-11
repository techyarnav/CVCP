import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, Database, Shield, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';

interface MetadataCardProps {
  processingTime: number;
  cacheUsed: boolean;
  rateLimited: boolean;
  updateCount: number;
  lastUpdated: number;
  isActive: boolean;
  delay?: number;
}

const MetadataCard: React.FC<MetadataCardProps> = ({ 
  processingTime, 
  cacheUsed, 
  rateLimited, 
  updateCount, 
  lastUpdated, 
  isActive,
  delay = 0 
}) => {
  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <Card 
      className="glass p-6 hover:scale-105 transition-transform duration-300 animate-slide-in-up opacity-0 border-border/20"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-gradient-accent rounded-full flex items-center justify-center">
          <Database className="w-5 h-5 text-accent-foreground" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-card-foreground">Processing Details</h3>
          <p className="text-sm text-muted-foreground">Analysis metadata & status</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Processing Time */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-card-foreground">Processing Time</span>
          </div>
          <span className="text-sm font-bold text-card-foreground">
            {processingTime.toFixed(2)}s
          </span>
        </div>

        {/* Cache Status */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-secondary" />
            <span className="text-sm font-medium text-card-foreground">Cache Used</span>
          </div>
          <Badge variant={cacheUsed ? "default" : "secondary"}>
            {cacheUsed ? "Yes" : "No"}
          </Badge>
        </div>

        {/* Rate Limiting */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-orange-500" />
            <span className="text-sm font-medium text-card-foreground">Rate Limited</span>
          </div>
          <Badge variant={rateLimited ? "destructive" : "default"}>
            {rateLimited ? "Yes" : "No"}
          </Badge>
        </div>

        {/* Update Count */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-card-foreground">Update Count</span>
          </div>
          <span className="text-sm font-bold text-card-foreground">{updateCount}</span>
        </div>

        {/* Last Updated */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-green-500" />
            <span className="text-sm font-medium text-card-foreground">Last Updated</span>
          </div>
          <span className="text-sm text-muted-foreground">
            {formatTimestamp(lastUpdated)}
          </span>
        </div>

        {/* Active Status */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            {isActive ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-red-500" />
            )}
            <span className="text-sm font-medium text-card-foreground">Status</span>
          </div>
          <Badge variant={isActive ? "default" : "destructive"}>
            {isActive ? "Active" : "Inactive"}
          </Badge>
        </div>
      </div>
    </Card>
  );
};

export default MetadataCard; 