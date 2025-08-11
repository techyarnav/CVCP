import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Activity, 
  Coins, 
  Shield, 
  TrendingUp, 
  Zap, 
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Info,
  RefreshCw,
  Brain
} from 'lucide-react';
import ParticleBackground from '@/components/ParticleBackground';
import ScoreCard from '@/components/ScoreCard';
import CircularProgress from '@/components/CircularProgress';
import LoadingSpinner from '@/components/LoadingSpinner';
import AIAnalysisCard from '@/components/AIAnalysisCard';
import MetadataCard from '@/components/MetadataCard';
import { creditScoreApi, CreditScoreResponse } from '@/services/creditScoreApi';
import heroBg from '@/assets/hero-bg.jpg';



const Index = () => {
  const [walletAddress, setWalletAddress] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [creditScoreData, setCreditScoreData] = useState<CreditScoreResponse | null>(null);
  const [isValidAddress, setIsValidAddress] = useState(true);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  const validateAddress = (address: string) => {
    const isValid = /^0x[a-fA-F0-9]{40}$/.test(address);
    setIsValidAddress(isValid || address === '');
    return isValid;
  };

  const handleAddressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const address = e.target.value;
    setWalletAddress(address);
    validateAddress(address);
  };

  const analyzeCreditScore = async () => {
    if (!validateAddress(walletAddress)) return;

    setIsLoading(true);
    setShowResults(false);
    setError(null);

    try {
      const response = await creditScoreApi.calculateScore({
        address: walletAddress,
        force_refresh: forceRefresh
      });

      if (response.success) {
        setCreditScoreData(response);
        setShowResults(true);
      } else {
        setError(response.error || 'Failed to calculate credit score');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while analyzing the address');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Set demo address on load
    setWalletAddress('0x742d35Cc6654c967e5c749CB1b5B43cA2E9b0b70');
    
    // Check backend health on component mount
    const checkBackendHealth = async () => {
      try {
        const isHealthy = await creditScoreApi.checkBackendHealth();
        setBackendStatus(isHealthy ? 'online' : 'offline');
      } catch (error) {
        setBackendStatus('offline');
      }
    };
    
    checkBackendHealth();
  }, []);

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <ParticleBackground />
      
      {/* Hero Background */}
      <div 
        className="absolute inset-0 z-0 opacity-30"
        style={{
          backgroundImage: `url(${heroBg})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed'
        }}
      />
      
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header Section */}
        <header className="text-center mb-16 animate-slide-in-up">
          <h1 className="text-6xl font-bold gradient-text mb-6">
            CryptoVault Credit Protocol
          </h1>
          <p className="text-xl text-muted-foreground mb-4">
            Advanced DeFi Credit Scoring on Scroll Sepolia
          </p>
          <div className="flex items-center gap-4">
            <Badge variant="outline" className="text-primary border-primary/50">
              CVCP v2.0 • Powered by Scroll
            </Badge>
            <Badge 
              variant={backendStatus === 'online' ? 'default' : backendStatus === 'checking' ? 'secondary' : 'destructive'}
              className="flex items-center gap-2"
            >
              <div className={`w-2 h-2 rounded-full ${
                backendStatus === 'online' ? 'bg-green-400' : 
                backendStatus === 'checking' ? 'bg-yellow-400' : 'bg-red-400'
              }`} />
              Backend: {backendStatus === 'checking' ? 'Checking...' : backendStatus === 'online' ? 'Online' : 'Offline'}
            </Badge>
          </div>
        </header>

        {/* Main Input Section */}
        <div className="max-w-2xl mx-auto mb-16 animate-slide-in-up delay-200">
          <Card className="glass p-8 border-border/20">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-3">
                  Wallet Address
                </label>
                <Input
                  type="text"
                  placeholder="0x742d35Cc6654c967e5c749CB1b5B43cA2E9b0b70"
                  value={walletAddress}
                  onChange={handleAddressChange}
                  className={`input-glow text-lg py-6 bg-background-secondary border-border/50 ${
                    !isValidAddress ? 'border-destructive focus:border-destructive' : ''
                  }`}
                />
                {!isValidAddress && (
                  <p className="text-destructive text-sm mt-2 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Please enter a valid Ethereum wallet address
                  </p>
                )}
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="forceRefresh"
                  checked={forceRefresh}
                  onChange={(e) => setForceRefresh(e.target.checked)}
                  className="w-4 h-4 text-primary bg-background border-border rounded focus:ring-primary focus:ring-2"
                />
                <label htmlFor="forceRefresh" className="text-sm text-muted-foreground flex items-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  Force refresh (bypass cache)
                </label>
              </div>
              
              <Button
                onClick={analyzeCreditScore}
                disabled={isLoading || !walletAddress || !isValidAddress}
                className="btn-primary w-full py-6 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <div className="flex items-center gap-3">
                    <LoadingSpinner size="sm" />
                    Analyzing blockchain data...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Zap className="w-5 h-5" />
                    Analyze Credit Score
                  </div>
                )}
              </Button>
            </div>
          </Card>
        </div>

        {/* Error Display */}
        {error && (
          <div className="max-w-2xl mx-auto mb-8 animate-slide-in-up">
            <Card className="glass p-6 border-destructive/50 bg-destructive/10">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-destructive" />
                <div>
                  <h3 className="font-semibold text-destructive">Error</h3>
                  <p className="text-sm text-destructive/80">{error}</p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Results Dashboard */}
        {showResults && creditScoreData && creditScoreData.credit_score && (
          <div className="space-y-8 animate-slide-in-up delay-300">
            {/* Main Score Display */}
            <div className="text-center mb-12">
              <CircularProgress 
                score={creditScoreData.credit_score?.totalScore || 0} 
                className="mx-auto mb-6"
              />
              <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-secondary" />
                  Confidence: {creditScoreData.credit_score?.confidence || 0}%
                </div>
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-primary" />
                  Updated: {creditScoreData.credit_score?.lastUpdated ? new Date(creditScoreData.credit_score.lastUpdated * 1000).toLocaleString() : 'Unknown'}
                </div>
              </div>
            </div>

            {/* Component Scores */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
              <ScoreCard
                title="Transaction Score"
                score={creditScoreData.credit_score?.transactionScore || 0}
                maxScore={100}
                icon={<Activity />}
                delay={0.1}
              />
              <ScoreCard
                title="DeFi Score"
                score={creditScoreData.credit_score?.defiScore || 0}
                maxScore={100}
                icon={<Coins />}
                delay={0.2}
              />
              <ScoreCard
                title="Staking Score"
                score={creditScoreData.credit_score?.stakingScore || 0}
                maxScore={100}
                icon={<TrendingUp />}
                delay={0.3}
              />
              <ScoreCard
                title="Risk Score"
                score={creditScoreData.credit_score?.riskScore || 0}
                maxScore={200}
                icon={<Shield />}
                delay={0.4}
              />
              <ScoreCard
                title="History Score"
                score={creditScoreData.credit_score?.historyScore || 0}
                maxScore={100}
                icon={<TrendingUp />}
                delay={0.5}
              />
            </div>

            {/* AI Analysis and Metadata */}
            <div className="grid md:grid-cols-2 gap-6 mb-12">
              {creditScoreData.ai_analysis ? (
                <AIAnalysisCard 
                  analysis={creditScoreData.ai_analysis}
                  delay={0.6}
                />
              ) : (
                <Card className="glass p-6 border-border/20 animate-slide-in-up opacity-0" style={{ animationDelay: '0.6s' }}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-primary rounded-full flex items-center justify-center">
                      <Brain className="w-5 h-5 text-primary-foreground" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-card-foreground">AI Analysis</h3>
                      <p className="text-sm text-muted-foreground">Powered by Gemini AI</p>
                    </div>
                  </div>
                  <div className="text-center py-8">
                    <p className="text-muted-foreground mb-2">AI analysis not available</p>
                    <p className="text-xs text-muted-foreground">This may be due to rate limiting or temporary service unavailability</p>
                  </div>
                </Card>
              )}
              <MetadataCard
                processingTime={creditScoreData.processing_time_seconds || 0}
                cacheUsed={creditScoreData.cache_used || false}
                rateLimited={creditScoreData.rate_limited || false}
                updateCount={creditScoreData.credit_score?.updateCount || 0}
                lastUpdated={creditScoreData.credit_score?.lastUpdated || Date.now() / 1000}
                isActive={creditScoreData.credit_score?.isActive || false}
                delay={0.7}
              />
            </div>

            {/* Additional Info */}
            <div className="grid md:grid-cols-2 gap-6">
              <Card className="glass p-6 border-border/20 animate-slide-in-up delay-800">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Info className="w-5 h-5 text-primary" />
                  Protocol Information
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Network</span>
                    <span className="text-card-foreground">Scroll Sepolia</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Address</span>
                    <span className="text-card-foreground font-mono text-xs">
                      {creditScoreData.address ? `${creditScoreData.address.slice(0, 10)}...${creditScoreData.address.slice(-8)}` : 'Unknown'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Algorithm Version</span>
                    <span className="text-card-foreground">CVCP v2.0</span>
                  </div>
                </div>
              </Card>

              <Card className="glass p-6 border-border/20 animate-slide-in-up delay-900">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <ExternalLink className="w-5 h-5 text-primary" />
                  Blockchain Explorer
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  View the address on Scroll Sepolia explorer
                </p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full border-primary/50 text-primary hover:bg-primary/10"
                  onClick={() => creditScoreData.address ? window.open(`https://sepolia.scrollscan.com/address/${creditScoreData.address}`, '_blank') : null}
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Address
                </Button>
              </Card>
            </div>
          </div>
        )}

        {/* How it Works Section */}
        <div className="mt-24 animate-slide-in-up delay-800">
          <Card className="glass p-8 border-border/20">
            <h2 className="text-3xl font-bold gradient-text mb-6 text-center">
              How It Works
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-4">
                  <Activity className="w-8 h-8 text-primary-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Data Collection</h3>
                <p className="text-sm text-muted-foreground">
                  Analyze on-chain transaction history, DeFi interactions, and staking patterns
                </p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-accent rounded-full flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-accent-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Risk Analysis</h3>
                <p className="text-sm text-muted-foreground">
                  AI-powered algorithms assess financial behavior and risk factors
                </p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-8 h-8 text-secondary-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Score Generation</h3>
                <p className="text-sm text-muted-foreground">
                  Generate comprehensive credit score (300-850) with confidence metrics
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Index;
