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
  Info
} from 'lucide-react';
import ParticleBackground from '@/components/ParticleBackground';
import ScoreCard from '@/components/ScoreCard';
import CircularProgress from '@/components/CircularProgress';
import LoadingSpinner from '@/components/LoadingSpinner';
import heroBg from '@/assets/hero-bg.jpg';

interface CreditScore {
  total: number;
  components: {
    transactionActivity: { score: number; weight: number };
    defiInteractions: { score: number; weight: number };
    stakingBehavior: { score: number; weight: number };
    riskAssessment: { score: number; weight: number };
    historicalPatterns: { score: number; weight: number };
  };
  confidence: number;
  lastUpdated: string;
  transactionHash: string;
}

const Index = () => {
  const [walletAddress, setWalletAddress] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [creditScore, setCreditScore] = useState<CreditScore | null>(null);
  const [isValidAddress, setIsValidAddress] = useState(true);
  const [showResults, setShowResults] = useState(false);

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

  const simulateAnalysis = async () => {
    if (!validateAddress(walletAddress)) return;

    setIsLoading(true);
    setShowResults(false);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Mock credit score data
    const mockScore: CreditScore = {
      total: 742,
      components: {
        transactionActivity: { score: 185, weight: 25 },
        defiInteractions: { score: 160, weight: 20 },
        stakingBehavior: { score: 190, weight: 25 },
        riskAssessment: { score: 152, weight: 20 },
        historicalPatterns: { score: 89, weight: 10 }
      },
      confidence: 87,
      lastUpdated: new Date().toLocaleString(),
      transactionHash: '0x8e9288aD536Ee22Df91026BE96cB1deE904C05eF'
    };

    setCreditScore(mockScore);
    setIsLoading(false);
    setShowResults(true);
  };

  useEffect(() => {
    // Set demo address on load
    setWalletAddress('0x742d35Cc6654c967e5c749CB1b5B43cA2E9b0b70');
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
          <Badge variant="outline" className="text-primary border-primary/50">
            CVCP v2.0 • Powered by Scroll
          </Badge>
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
              
              <Button
                onClick={simulateAnalysis}
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

        {/* Results Dashboard */}
        {showResults && creditScore && (
          <div className="space-y-8 animate-slide-in-up delay-300">
            {/* Main Score Display */}
            <div className="text-center mb-12">
              <CircularProgress 
                score={creditScore.total} 
                className="mx-auto mb-6"
              />
              <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-secondary" />
                  Confidence: {creditScore.confidence}%
                </div>
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-primary" />
                  Updated: {creditScore.lastUpdated}
                </div>
              </div>
            </div>

            {/* Component Scores */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
              <ScoreCard
                title="Transaction Activity"
                score={creditScore.components.transactionActivity.score}
                maxScore={200}
                weight={creditScore.components.transactionActivity.weight}
                icon={<Activity />}
                delay={0.1}
              />
              <ScoreCard
                title="DeFi Interactions"
                score={creditScore.components.defiInteractions.score}
                maxScore={200}
                weight={creditScore.components.defiInteractions.weight}
                icon={<Coins />}
                delay={0.2}
              />
              <ScoreCard
                title="Staking Behavior"
                score={creditScore.components.stakingBehavior.score}
                maxScore={200}
                weight={creditScore.components.stakingBehavior.weight}
                icon={<TrendingUp />}
                delay={0.3}
              />
              <ScoreCard
                title="Risk Assessment"
                score={creditScore.components.riskAssessment.score}
                maxScore={200}
                weight={creditScore.components.riskAssessment.weight}
                icon={<Shield />}
                delay={0.4}
              />
              <ScoreCard
                title="Historical Patterns"
                score={creditScore.components.historicalPatterns.score}
                maxScore={200}
                weight={creditScore.components.historicalPatterns.weight}
                icon={<TrendingUp />}
                delay={0.5}
              />
            </div>

            {/* Additional Info */}
            <div className="grid md:grid-cols-2 gap-6">
              <Card className="glass p-6 border-border/20 animate-slide-in-up delay-600">
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
                    <span className="text-muted-foreground">Contract</span>
                    <span className="text-card-foreground font-mono text-xs">
                      {creditScore.transactionHash.slice(0, 10)}...
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Algorithm Version</span>
                    <span className="text-card-foreground">CVCP v2.0</span>
                  </div>
                </div>
              </Card>

              <Card className="glass p-6 border-border/20 animate-slide-in-up delay-700">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <ExternalLink className="w-5 h-5 text-primary" />
                  Blockchain Explorer
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  View the transaction on Scroll Sepolia explorer
                </p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full border-primary/50 text-primary hover:bg-primary/10"
                  onClick={() => window.open(`https://sepolia.scrollscan.com/tx/${creditScore.transactionHash}`, '_blank')}
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Transaction
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
