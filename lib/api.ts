// CARMA Vehicle Comparison API Service
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://carma-ml-api.greenwater-7817a41f.northeurope.azurecontainerapps.io';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Utility function for retrying API calls
async function retryApiCall<T>(
  apiCall: () => Promise<T>,
  maxRetries: number = MAX_RETRIES,
  delay: number = RETRY_DELAY
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on client errors (4xx)
      if (error instanceof Error && error.message.includes('HTTP 4')) {
        throw error;
      }
      
      // Don't retry on the last attempt
      if (attempt === maxRetries) {
        break;
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
    }
  }
  
  throw lastError!;
}

export interface Vehicle {
  id: string;
  url: string;
  price_eur: number;
  price_hat: number;
  deal_score: number;
  mileage_km: number;
  year: number;
  make: string;
  model: string;
  fuel_group: string;
  transmission_group: string;
  body_group: string;
  description: string;
  data_source: string;
  power_kw?: number;
  score?: number; // Similarity score for comparable vehicles
  images?: string[]; // Vehicle images
  exterior_color?: string;
  interior_color?: string;
  upholstery_color?: string;
}

export interface ApiStats {
  total_vehicles: number;
  unique_makes: number;
  data_sources: number;
  status: string;
}

export interface ApiHealth {
  status: string;
  database_connected: boolean;
  timestamp: string;
}

// Extract vehicle ID from AutoScout24 URL
export function extractVehicleId(input: string): string {
  if (input.includes('autoscout24.de')) {
    const parts = input.split('/');
    const lastPart = parts[parts.length - 1];
    
    // Extract UUID from the last part of the URL
    // AutoScout24 URLs have format: ...-uuid
    const uuidMatch = lastPart.match(/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$/);
    if (uuidMatch) {
      return uuidMatch[1];
    }
    
    // Fallback: return the last part if no UUID pattern found
    return lastPart;
  }
  return input.trim();
}

// Validate vehicle ID format (UUID format)
export function validateVehicleId(vehicleId: string): boolean {
  const pattern = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
  return pattern.test(vehicleId);
}

// Check API health
export async function checkApiHealth(): Promise<ApiHealth> {
  return retryApiCall(async () => {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  });
}

// Get database statistics
export async function getDatabaseStats(): Promise<ApiStats> {
  return retryApiCall(async () => {
    const response = await fetch(`${API_BASE}/database/stats`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  });
}

// Get vehicle details
export async function getVehicleDetails(vehicleId: string): Promise<Vehicle> {
  return retryApiCall(async () => {
    const response = await fetch(`${API_BASE}/listings/${vehicleId}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Vehicle not found. Please check the URL and try again.');
      } else if (response.status === 500) {
        throw new Error('Server error. Please try again later.');
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    }
    return await response.json();
  });
}

// Get comparable vehicles
export async function getComparableVehicles(vehicleId: string, top: number = 10): Promise<Vehicle[]> {
  return retryApiCall(async () => {
    const response = await fetch(`${API_BASE}/listings/${vehicleId}/comparables?top=${top}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('No comparable vehicles found for this vehicle.');
      } else if (response.status === 500) {
        throw new Error('Server error. Please try again later.');
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    }
    return await response.json();
  });
}

// API health monitoring
export class ApiHealthMonitor {
  private static instance: ApiHealthMonitor;
  private healthStatus: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
  private lastCheck: Date | null = null;
  private consecutiveFailures = 0;

  static getInstance(): ApiHealthMonitor {
    if (!ApiHealthMonitor.instance) {
      ApiHealthMonitor.instance = new ApiHealthMonitor();
    }
    return ApiHealthMonitor.instance;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const health = await checkApiHealth();
      this.healthStatus = health.database_connected ? 'healthy' : 'degraded';
      this.consecutiveFailures = 0;
      this.lastCheck = new Date();
      return true;
    } catch (error) {
      this.consecutiveFailures++;
      this.lastCheck = new Date();
      
      if (this.consecutiveFailures >= 3) {
        this.healthStatus = 'unhealthy';
      } else {
        this.healthStatus = 'degraded';
      }
      
      return false;
    }
  }

  getStatus(): { status: string; lastCheck: Date | null; consecutiveFailures: number } {
    return {
      status: this.healthStatus,
      lastCheck: this.lastCheck,
      consecutiveFailures: this.consecutiveFailures
    };
  }

  isHealthy(): boolean {
    return this.healthStatus === 'healthy';
  }
}

// Main comparison function
export async function compareVehicle(input: string): Promise<{ vehicle: Vehicle; comparables: Vehicle[] }> {
  const vehicleId = extractVehicleId(input);
  
  if (!validateVehicleId(vehicleId)) {
    throw new Error('Invalid vehicle URL or ID format. Please use a valid AutoScout24 URL.');
  }

  try {
    const [vehicleDetails, comparables] = await Promise.all([
      getVehicleDetails(vehicleId),
      getComparableVehicles(vehicleId, 50)
    ]);

    return {
      vehicle: vehicleDetails,
      comparables
    };
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error(`Vehicle comparison failed: ${error}`);
  }
}

// Format deal score for display
export function formatDealScore(score: number): { text: string; class: string; isGood: boolean } {
  const percentage = Math.abs(score * 100).toFixed(1);
  
  if (score > 0) {
    return {
      text: `Good Deal (+${percentage}%)`,
      class: 'text-green-600',
      isGood: true
    };
  } else if (score < 0) {
    return {
      text: `Overpriced (${percentage}%)`,
      class: 'text-red-600',
      isGood: false
    };
  } else {
    return {
      text: 'Fair Price',
      class: 'text-gray-600',
      isGood: true
    };
  }
}

// Format price for display
export function formatPrice(price: number): string {
  // Handle the API price parsing issue where €16,480 becomes 16.0
  // If price is suspiciously low (less than 1000), try to reconstruct from URL
  let adjustedPrice = price;
  
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(adjustedPrice);
}

// Format mileage for display
export function formatMileage(mileage: number): string {
  return new Intl.NumberFormat('de-DE').format(mileage) + ' km';
}
