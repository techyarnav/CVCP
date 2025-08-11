// Example usage of the credit score API service
import { creditScoreApi } from '@/services/creditScoreApi';

// Example 1: Calculate credit score for an address
export const calculateScoreExample = async () => {
  try {
    const result = await creditScoreApi.calculateScore({
      address: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
      force_refresh: false
    });
    
    console.log('Credit Score Result:', result);
    return result;
  } catch (error) {
    console.error('Error calculating score:', error);
    throw error;
  }
};

// Example 2: Check backend health
export const checkBackendHealthExample = async () => {
  try {
    const isHealthy = await creditScoreApi.checkBackendHealth();
    console.log('Backend Health:', isHealthy ? 'Online' : 'Offline');
    return isHealthy;
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

// Example 3: Get backend status
export const getBackendStatusExample = async () => {
  try {
    const status = await creditScoreApi.getBackendStatus();
    console.log('Backend Status:', status);
    return status;
  } catch (error) {
    console.error('Status check failed:', error);
    throw error;
  }
};

// Example 4: Batch address processing
export const batchProcessAddresses = async (addresses: string[]) => {
  const results = [];
  
  for (const address of addresses) {
    try {
      const result = await creditScoreApi.calculateScore({
        address,
        force_refresh: false
      });
      results.push({ address, success: true, data: result });
    } catch (error) {
      results.push({ address, success: false, error: error instanceof Error ? error.message : 'Unknown error' });
    }
  }
  
  return results;
};

// Example 5: Error handling with retry logic
export const calculateScoreWithRetry = async (
  address: string, 
  maxRetries: number = 3,
  delayMs: number = 1000
) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await creditScoreApi.calculateScore({
        address,
        force_refresh: false
      });
      return result;
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      
      console.log(`Attempt ${attempt} failed, retrying in ${delayMs}ms...`);
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }
}; 