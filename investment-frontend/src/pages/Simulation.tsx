import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { TrendingUp, Play, DollarSign, Calendar, Percent } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { simulationApi } from '@/api/client';
import type { MonteCarloResult, FundDepletionResult } from '@/types';

function formatCurrency(value: number): string {
  if (value >= 100000000) {
    const oku = Math.floor(value / 100000000);
    const man = Math.floor((value % 100000000) / 10000);
    if (man > 0) {
      return `${oku.toLocaleString()}億${man.toLocaleString()}万円`;
    }
    return `${oku.toLocaleString()}億円`;
  } else if (value >= 10000) {
    return `${Math.floor(value / 10000).toLocaleString()}万円`;
  }
  return `${value.toLocaleString()}円`;
}

function formatYAxis(value: number): string {
  if (value >= 100000000) {
    return `${(value / 100000000).toFixed(0)}億`;
  } else if (value >= 10000) {
    return `${(value / 10000).toFixed(0)}万`;
  }
  return value.toString();
}

export default function Simulation() {
  const [simulationType, setSimulationType] = useState<'monte_carlo' | 'fund_depletion'>('monte_carlo');
  const [loading, setLoading] = useState(false);
  
  const [monteCarloParams, setMonteCarloParams] = useState({
    initial_amount: 10000000,
    monthly_contribution: 50000,
    years: 20,
    expected_return: 0.05,
    volatility: 0.15,
    num_simulations: 1000,
  });
  
  const [fundDepletionParams, setFundDepletionParams] = useState({
    initial_amount: 30000000,
    monthly_withdrawal: 200000,
    expected_return: 0.03,
    volatility: 0.10,
    max_years: 40,
  });
  
  const [monteCarloResult, setMonteCarloResult] = useState<MonteCarloResult | null>(null);
  const [fundDepletionResult, setFundDepletionResult] = useState<FundDepletionResult | null>(null);

  const runMonteCarlo = async () => {
    setLoading(true);
    try {
      const result = await simulationApi.runMonteCarlo(monteCarloParams);
      setMonteCarloResult(result);
    } catch (error) {
      console.error('Monte Carlo simulation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const runFundDepletion = async () => {
    setLoading(true);
    try {
      const result = await simulationApi.runFundDepletion(fundDepletionParams);
      setFundDepletionResult(result);
    } catch (error) {
      console.error('Fund depletion simulation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = monteCarloResult?.percentile_paths ? 
    monteCarloResult.percentile_paths.p50.map((value, index) => ({
      year: index,
      p5: monteCarloResult.percentile_paths.p5[index],
      p25: monteCarloResult.percentile_paths.p25[index],
      p50: value,
      p75: monteCarloResult.percentile_paths.p75[index],
      p95: monteCarloResult.percentile_paths.p95[index],
    })) : [];

  const depletionChartData = fundDepletionResult?.yearly_balances ?
    fundDepletionResult.yearly_balances.map((balance, index) => ({
      year: index,
      balance,
    })) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">シミュレーション</h1>
        <p className="text-gray-600 mt-1">将来の資産推移をシミュレーション</p>
      </div>

      <div className="flex gap-2">
        <Button
          variant={simulationType === 'monte_carlo' ? 'default' : 'outline'}
          onClick={() => setSimulationType('monte_carlo')}
        >
          <TrendingUp className="h-4 w-4 mr-2" />
          モンテカルロ・シミュレーション
        </Button>
        <Button
          variant={simulationType === 'fund_depletion' ? 'default' : 'outline'}
          onClick={() => setSimulationType('fund_depletion')}
        >
          <Calendar className="h-4 w-4 mr-2" />
          資産取り崩しシミュレーション
        </Button>
      </div>

      {simulationType === 'monte_carlo' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>パラメータ設定</CardTitle>
              <CardDescription>シミュレーション条件を設定</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  初期投資額（円）
                </Label>
                <Input
                  type="number"
                  value={monteCarloParams.initial_amount}
                  onChange={(e) => setMonteCarloParams({ ...monteCarloParams, initial_amount: parseInt(e.target.value) || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  毎月積立額（円）
                </Label>
                <Input
                  type="number"
                  value={monteCarloParams.monthly_contribution}
                  onChange={(e) => setMonteCarloParams({ ...monteCarloParams, monthly_contribution: parseInt(e.target.value) || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  投資期間（年）
                </Label>
                <Input
                  type="number"
                  value={monteCarloParams.years}
                  onChange={(e) => setMonteCarloParams({ ...monteCarloParams, years: parseInt(e.target.value) || 1 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="flex items-center gap-2">
                  <Percent className="h-4 w-4" />
                  期待リターン（年率 %）
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  value={(monteCarloParams.expected_return * 100).toFixed(1)}
                  onChange={(e) => setMonteCarloParams({ ...monteCarloParams, expected_return: parseFloat(e.target.value) / 100 || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="flex items-center gap-2">
                  <Percent className="h-4 w-4" />
                  リスク（標準偏差 %）
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  value={(monteCarloParams.volatility * 100).toFixed(1)}
                  onChange={(e) => setMonteCarloParams({ ...monteCarloParams, volatility: parseFloat(e.target.value) / 100 || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label>シミュレーション回数</Label>
                <Input
                  type="number"
                  value={monteCarloParams.num_simulations}
                  onChange={(e) => setMonteCarloParams({ ...monteCarloParams, num_simulations: parseInt(e.target.value) || 100 })}
                  className="mt-1"
                />
              </div>
              <Button onClick={runMonteCarlo} className="w-full" disabled={loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    実行中...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Play className="h-4 w-4" />
                    シミュレーション実行
                  </span>
                )}
              </Button>
            </CardContent>
          </Card>

          <div className="lg:col-span-2 space-y-6">
            {monteCarloResult && (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>シミュレーション結果</CardTitle>
                    <CardDescription>資産推移の予測（パーセンタイル）</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="year" label={{ value: '年', position: 'insideBottomRight', offset: -5 }} />
                          <YAxis tickFormatter={formatYAxis} />
                          <Tooltip
                            formatter={(value: number) => formatCurrency(value)}
                            labelFormatter={(label) => `${label}年後`}
                          />
                          <Area type="monotone" dataKey="p95" stackId="1" stroke="#22c55e" fill="#dcfce7" name="95パーセンタイル" />
                          <Area type="monotone" dataKey="p75" stackId="2" stroke="#3b82f6" fill="#dbeafe" name="75パーセンタイル" />
                          <Line type="monotone" dataKey="p50" stroke="#1d4ed8" strokeWidth={2} name="中央値" dot={false} />
                          <Area type="monotone" dataKey="p25" stackId="3" stroke="#f59e0b" fill="#fef3c7" name="25パーセンタイル" />
                          <Area type="monotone" dataKey="p5" stackId="4" stroke="#ef4444" fill="#fee2e2" name="5パーセンタイル" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-sm text-gray-600">期待最終資産</div>
                      <div className="text-xl font-bold text-blue-600">{formatCurrency(monteCarloResult.expected_final_value)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-sm text-gray-600">中央値</div>
                      <div className="text-xl font-bold text-green-600">{formatCurrency(monteCarloResult.median_final_value)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-sm text-gray-600">5%タイル（悲観）</div>
                      <div className="text-xl font-bold text-red-600">{formatCurrency(monteCarloResult.percentile_5)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-sm text-gray-600">95%タイル（楽観）</div>
                      <div className="text-xl font-bold text-green-600">{formatCurrency(monteCarloResult.percentile_95)}</div>
                    </CardContent>
                  </Card>
                </div>
              </>
            )}

            {!monteCarloResult && (
              <Card>
                <CardContent className="py-16 text-center text-gray-500">
                  パラメータを設定してシミュレーションを実行してください
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}

      {simulationType === 'fund_depletion' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>パラメータ設定</CardTitle>
              <CardDescription>取り崩し条件を設定</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  初期資産額（円）
                </Label>
                <Input
                  type="number"
                  value={fundDepletionParams.initial_amount}
                  onChange={(e) => setFundDepletionParams({ ...fundDepletionParams, initial_amount: parseInt(e.target.value) || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  毎月取り崩し額（円）
                </Label>
                <Input
                  type="number"
                  value={fundDepletionParams.monthly_withdrawal}
                  onChange={(e) => setFundDepletionParams({ ...fundDepletionParams, monthly_withdrawal: parseInt(e.target.value) || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="flex items-center gap-2">
                  <Percent className="h-4 w-4" />
                  期待リターン（年率 %）
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  value={(fundDepletionParams.expected_return * 100).toFixed(1)}
                  onChange={(e) => setFundDepletionParams({ ...fundDepletionParams, expected_return: parseFloat(e.target.value) / 100 || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="flex items-center gap-2">
                  <Percent className="h-4 w-4" />
                  リスク（標準偏差 %）
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  value={(fundDepletionParams.volatility * 100).toFixed(1)}
                  onChange={(e) => setFundDepletionParams({ ...fundDepletionParams, volatility: parseFloat(e.target.value) / 100 || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  最大シミュレーション期間（年）
                </Label>
                <Input
                  type="number"
                  value={fundDepletionParams.max_years}
                  onChange={(e) => setFundDepletionParams({ ...fundDepletionParams, max_years: parseInt(e.target.value) || 1 })}
                  className="mt-1"
                />
              </div>
              <Button onClick={runFundDepletion} className="w-full" disabled={loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    実行中...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Play className="h-4 w-4" />
                    シミュレーション実行
                  </span>
                )}
              </Button>
            </CardContent>
          </Card>

          <div className="lg:col-span-2 space-y-6">
            {fundDepletionResult && (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>資産推移予測</CardTitle>
                    <CardDescription>取り崩しによる資産残高の推移</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={depletionChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="year" label={{ value: '年', position: 'insideBottomRight', offset: -5 }} />
                          <YAxis tickFormatter={formatYAxis} />
                          <Tooltip
                            formatter={(value: number) => formatCurrency(value)}
                            labelFormatter={(label) => `${label}年後`}
                          />
                          <Line type="monotone" dataKey="balance" stroke="#3b82f6" strokeWidth={2} name="資産残高" dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-sm text-gray-600">資産枯渇年数</div>
                      <div className="text-xl font-bold text-blue-600">
                        {fundDepletionResult.depletion_year ? `${fundDepletionResult.depletion_year}年` : '枯渇しない'}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-sm text-gray-600">枯渇確率</div>
                      <div className="text-xl font-bold text-red-600">{(fundDepletionResult.depletion_probability * 100).toFixed(1)}%</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-sm text-gray-600">安全取り崩し率</div>
                      <div className="text-xl font-bold text-green-600">{(fundDepletionResult.safe_withdrawal_rate * 100).toFixed(1)}%</div>
                    </CardContent>
                  </Card>
                </div>
              </>
            )}

            {!fundDepletionResult && (
              <Card>
                <CardContent className="py-16 text-center text-gray-500">
                  パラメータを設定してシミュレーションを実行してください
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
