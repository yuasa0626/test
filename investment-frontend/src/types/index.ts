// Types for the Investment Portfolio API

export interface FamilyMember {
  name: string;
  age: number;
}

export interface Liability {
  type: 'housing' | 'car' | 'education' | 'other';
  name: string;
  balance: number;
  interest_rate: number;
  monthly_payment: number;
  remaining_years: number;
}

export interface UserProfile {
  age: number;
  occupation: string;
  annual_income: number;
  annual_expense: number;
  monthly_investment: number;
  savings: number;
  emergency_fund: number;
  family_members: FamilyMember[];
  liabilities: Liability[];
}

export interface PortfolioHolding {
  ticker: string;
  name: string;
  amount: number;
  asset_class: string;
  account_type: string;
}

export interface EducationPath {
  name: string;
  description: string;
}

export interface EducationCostResult {
  total_cost: number;
  breakdown: Record<string, number>;
  path_name: string;
  path_description: string;
  living_away: boolean;
  note: string;
}

export interface AssetClass {
  id: string;
  name: string;
  expected_return: number;
  volatility: number;
}

export interface PortfolioMetrics {
  total_value: number;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  var_95: number;
  cvar_95: number;
  asset_allocation: Record<string, number>;
}

export interface MonteCarloResult {
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
}

export interface StressTestResult {
  scenario_id: string;
  scenario_name: string;
  scenario_description: string;
  portfolio_loss: number;
  loss_amount: number;
  post_crisis_value: number;
  asset_class_impacts: Record<string, number>;
}

export interface RebalanceAction {
  asset_class: string;
  asset_name: string;
  action: 'buy' | 'sell';
  current_weight: number;
  target_weight: number;
  amount: number;
}

export interface NISAOptimizationResult {
  current_nisa_total: number;
  current_tokutei_total: number;
  recommended_moves: Array<{
    ticker: string;
    name: string;
    current_value: number;
    expected_return: number;
    estimated_tax_savings_10y: number;
    priority: string;
  }>;
  estimated_tax_savings: number;
  note: string;
}

export interface FundDepletionResult {
  depletion_year: number | null;
  depletion_probability: number;
  safe_withdrawal_rate: number;
  yearly_balances: number[];
}
