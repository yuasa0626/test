import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Play, TrendingDown, Calendar, DollarSign } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { simulationApi } from '@/api/client';
import type { StressTestResult, PortfolioHolding } from '@/types';

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

interface Scenario {
  id: string;
  name: string;
  description: string;
  period: string;
  impact: Record<string, number>;
}

const SCENARIO_COLORS: Record<string, string> = {
  'lehman': '#ef4444',
  'covid': '#f59e0b',
  'dotcom': '#8b5cf6',
  'japan_bubble': '#3b82f6',
};

export default function StressTest() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<StressTestResult | null>(null);
  const [compareResults, setCompareResults] = useState<StressTestResult[]>([]);
  
  const [portfolio] = useState<PortfolioHolding[]>([
    { ticker: 'eMAXIS Slim 全世界株式', name: 'eMAXIS Slim 全世界株式（オール・カントリー）', amount: 3000000, asset_class: 'developed_stock', account_type: 'nisa_growth' },
    { ticker: 'eMAXIS Slim 国内株式', name: 'eMAXIS Slim 国内株式（TOPIX）', amount: 2000000, asset_class: 'domestic_stock', account_type: 'nisa_growth' },
    { ticker: 'eMAXIS Slim 先進国債券', name: 'eMAXIS Slim 先進国債券インデックス', amount: 1000000, asset_class: 'developed_bond', account_type: 'tokutei' },
  ]);

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      const data = await simulationApi.getStressTestScenarios();
      setScenarios(data);
      if (data.length > 0) {
        setSelectedScenario(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load scenarios:', error);
    }
  };

  const runStressTest = async () => {
    if (!selectedScenario) return;
    
    setLoading(true);
    try {
      const data = await simulationApi.runStressTest({
        holdings: portfolio,
        scenario_id: selectedScenario,
      });
      setResult(data);
    } catch (error) {
      console.error('Stress test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const runAllScenarios = async () => {
    setLoading(true);
    try {
      const results: StressTestResult[] = [];
      for (const scenario of scenarios) {
        const data = await simulationApi.runStressTest({
          holdings: portfolio,
          scenario_id: scenario.id,
        });
        results.push(data);
      }
      setCompareResults(results);
    } catch (error) {
      console.error('Stress test comparison failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalPortfolioValue = portfolio.reduce((sum, h) => sum + h.amount, 0);

  const comparisonChartData = compareResults.map((r) => ({
    name: r.scenario_name,
    loss: r.portfolio_loss * 100,
    scenarioId: r.scenario_id,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">ストレステスト</h1>
        <p className="text-gray-600 mt-1">歴史的な危機シナリオでポートフォリオを検証</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              シナリオ選択
            </CardTitle>
            <CardDescription>テストする危機シナリオを選択</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {scenarios.map((scenario) => (
                <div
                  key={scenario.id}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                    selectedScenario === scenario.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedScenario(scenario.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{scenario.name}</div>
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: SCENARIO_COLORS[scenario.id] || '#6b7280' }}
                    ></div>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">{scenario.description}</div>
                  <div className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {scenario.period}
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-2 pt-4">
              <Button onClick={runStressTest} className="w-full" disabled={loading || !selectedScenario}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    実行中...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Play className="h-4 w-4" />
                    ストレステスト実行
                  </span>
                )}
              </Button>
              <Button onClick={runAllScenarios} variant="outline" className="w-full" disabled={loading}>
                全シナリオ比較
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>現在のポートフォリオ</CardTitle>
              <CardDescription>ストレステスト対象の資産</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {portfolio.map((holding, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium text-sm">{holding.name}</div>
                      <div className="text-xs text-gray-500">{holding.asset_class}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{formatCurrency(holding.amount)}</div>
                      <div className="text-xs text-gray-500">
                        {((holding.amount / totalPortfolioValue) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                ))}
                <div className="flex items-center justify-between pt-3 border-t">
                  <span className="font-medium">合計</span>
                  <span className="text-xl font-bold">{formatCurrency(totalPortfolioValue)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-red-500" />
                  {result.scenario_name} の影響
                </CardTitle>
                <CardDescription>{result.scenario_description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                  <div className="p-4 bg-red-50 rounded-lg">
                    <div className="text-sm text-red-600 flex items-center gap-1">
                      <TrendingDown className="h-4 w-4" />
                      想定損失率
                    </div>
                    <div className="text-2xl font-bold text-red-700">
                      {(result.portfolio_loss * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <div className="text-sm text-red-600 flex items-center gap-1">
                      <DollarSign className="h-4 w-4" />
                      想定損失額
                    </div>
                    <div className="text-2xl font-bold text-red-700">
                      {formatCurrency(result.loss_amount)}
                    </div>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="text-sm text-blue-600 flex items-center gap-1">
                      <DollarSign className="h-4 w-4" />
                      危機後の資産
                    </div>
                    <div className="text-2xl font-bold text-blue-700">
                      {formatCurrency(result.post_crisis_value)}
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="text-sm font-medium text-gray-700">資産クラス別影響</div>
                  {Object.entries(result.asset_class_impacts).map(([assetClass, impact]) => (
                    <div key={assetClass} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{assetClass}</span>
                      <span className={`text-sm font-medium ${impact < 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {(impact * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {compareResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>シナリオ比較</CardTitle>
                <CardDescription>各危機シナリオでの想定損失率</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={comparisonChartData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" tickFormatter={(v) => `${v.toFixed(0)}%`} />
                      <YAxis type="category" dataKey="name" width={120} />
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                      <Bar dataKey="loss" name="損失率">
                        {comparisonChartData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={SCENARIO_COLORS[entry.scenarioId] || '#6b7280'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                  {compareResults.map((r) => (
                    <div key={r.scenario_id} className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-500">{r.scenario_name}</div>
                      <div className="text-lg font-bold text-red-600">
                        {formatCurrency(r.loss_amount)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {!result && compareResults.length === 0 && (
            <Card>
              <CardContent className="py-16 text-center text-gray-500">
                シナリオを選択してストレステストを実行してください
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
