// API Client for Investment Portfolio API

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// Cost APIs
export const costsApi = {
  getEducationPaths: () => fetchApi<{ paths: Record<string, { name: string; description: string }> }>('/api/costs/education/paths'),
  
  calculateEducationCost: (pathId: string, livingAway: boolean, inflationRate: number = 0.01) =>
    fetchApi<{
      total_cost: number;
      breakdown: Record<string, number>;
      path_name: string;
      path_description: string;
      living_away: boolean;
      note: string;
    }>('/api/costs/education/calculate', {
      method: 'POST',
      body: JSON.stringify({ path_id: pathId, living_away: livingAway, inflation_rate: inflationRate }),
    }),

  getHousingTypes: () => fetchApi<{ types: Record<string, string> }>('/api/costs/housing/types'),
  
  calculateHousingCost: (params: {
    housing_type: string;
    building_age: number;
    monthly_rent: number;
    loan_balance: number;
    loan_rate: number;
    loan_monthly_payment: number;
    loan_remaining_years: number;
    years_to_simulate: number;
  }) => fetchApi('/api/costs/housing/calculate', { method: 'POST', body: JSON.stringify(params) }),

  getVehicleTypes: () => fetchApi<{ types: Record<string, unknown> }>('/api/costs/vehicle/types'),
  
  getTravelTypes: () => fetchApi<{ types: Record<string, unknown> }>('/api/costs/travel/types'),
};

// Portfolio APIs
export const portfolioApi = {
  getAssetClasses: async () => {
    const response = await fetchApi<{ asset_classes: Record<string, { name: string; expected_return: number; volatility: number }> }>('/api/portfolio/asset-classes');
    return Object.entries(response.asset_classes).map(([id, data]) => ({
      id,
      name: data.name,
      expected_return: data.expected_return,
      volatility: data.volatility,
    }));
  },
  
  searchSecurities: async (query: string) => {
    const response = await fetchApi<{ results: Array<{ ticker: string; name: string; asset_class: string; expense_ratio: number }> }>(`/api/portfolio/securities/search?query=${encodeURIComponent(query)}`);
    return response.results;
  },
  
  listSecurities: async () => {
    const response = await fetchApi<{ securities: Array<{ ticker: string; name: string; asset_class: string; expense_ratio: number }> }>('/api/portfolio/securities');
    return response.securities;
  },
  
  analyzePortfolio: (holdings: Array<{
    ticker: string;
    name: string;
    amount: number;
    asset_class: string;
    account_type: string;
  }>) => fetchApi<{
    total_value: number;
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    var_95: number;
    cvar_95: number;
    asset_allocation: Record<string, number>;
  }>('/api/portfolio/analyze', { method: 'POST', body: JSON.stringify({ holdings }) }),

  getCorrelation: (holdings: Array<{
    ticker: string;
    name: string;
    amount: number;
  }>) => fetchApi('/api/portfolio/correlation', { method: 'POST', body: JSON.stringify({ holdings }) }),

  getEfficientFrontier: (holdings: Array<{
    ticker: string;
    name: string;
    amount: number;
  }>) => fetchApi('/api/portfolio/efficient-frontier', { method: 'POST', body: JSON.stringify({ holdings }) }),

  getRebalanceRecommendations: (holdings: Array<{
    ticker: string;
    name: string;
    amount: number;
  }>, targetAllocation?: Record<string, number>) => fetchApi('/api/portfolio/rebalance', {
    method: 'POST',
    body: JSON.stringify({ holdings, target_allocation: targetAllocation }),
  }),

  getNISAOptimization: (holdings: Array<{
    ticker: string;
    name: string;
    amount: number;
    account_type: string;
  }>) => fetchApi('/api/portfolio/nisa-optimization', { method: 'POST', body: JSON.stringify({ holdings }) }),
};

// Simulation APIs
export const simulationApi = {
  runMonteCarlo: (params: {
    initial_amount: number;
    monthly_contribution: number;
    years: number;
    expected_return: number;
    volatility: number;
    num_simulations: number;
  }) => fetchApi<{
    expected_final_value: number;
    median_final_value: number;
    percentile_5: number;
    percentile_95: number;
    percentile_paths: {
      p5: number[];
      p25: number[];
      p50: number[];
      p75: number[];
      p95: number[];
    };
    success_probability: number;
  }>('/api/simulation/monte-carlo', { method: 'POST', body: JSON.stringify(params) }),

  runFundDepletion: (params: {
    initial_amount: number;
    monthly_withdrawal: number;
    expected_return: number;
    volatility: number;
    max_years: number;
  }) => fetchApi<{
    depletion_year: number | null;
    depletion_probability: number;
    safe_withdrawal_rate: number;
    yearly_balances: number[];
  }>('/api/simulation/fund-depletion', { method: 'POST', body: JSON.stringify(params) }),

  getStressTestScenarios: async () => {
    const response = await fetchApi<{ scenarios: Record<string, { name: string; description: string; period: string; impact: Record<string, number> }> }>('/api/simulation/stress-test/scenarios');
    return Object.entries(response.scenarios).map(([id, data]) => ({
      id,
      name: data.name,
      description: data.description,
      period: data.period,
      impact: data.impact,
    }));
  },

  runStressTest: (params: {
    holdings: Array<{
      ticker: string;
      name: string;
      amount: number;
      asset_class: string;
      account_type: string;
    }>;
    scenario_id: string;
  }) => fetchApi<{
    scenario_id: string;
    scenario_name: string;
    scenario_description: string;
    portfolio_loss: number;
    loss_amount: number;
    post_crisis_value: number;
    asset_class_impacts: Record<string, number>;
  }>('/api/simulation/stress-test', {
    method: 'POST',
    body: JSON.stringify(params),
  }),
};

export { API_BASE_URL };
