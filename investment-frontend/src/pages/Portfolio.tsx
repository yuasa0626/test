import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Trash2, Search, PieChart, BarChart3 } from 'lucide-react';
import { portfolioApi } from '@/api/client';
import type { AssetClass, PortfolioHolding, PortfolioMetrics } from '@/types';

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

const ASSET_CLASS_COLORS: Record<string, string> = {
  'domestic_stock': 'bg-blue-500',
  'developed_stock': 'bg-green-500',
  'emerging_stock': 'bg-yellow-500',
  'domestic_bond': 'bg-purple-500',
  'developed_bond': 'bg-red-500',
  'emerging_bond': 'bg-orange-500',
  'domestic_reit': 'bg-pink-500',
  'global_reit': 'bg-indigo-500',
  'gold': 'bg-amber-500',
  'cash': 'bg-gray-500',
};

const ASSET_CLASS_NAMES: Record<string, string> = {
  'domestic_stock': '国内株式',
  'developed_stock': '先進国株式',
  'emerging_stock': '新興国株式',
  'domestic_bond': '国内債券',
  'developed_bond': '先進国債券',
  'emerging_bond': '新興国債券',
  'domestic_reit': '国内REIT',
  'global_reit': 'グローバルREIT',
  'gold': '金',
  'cash': '現金',
};

export default function Portfolio() {
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([
    { ticker: 'eMAXIS Slim 全世界株式', name: 'eMAXIS Slim 全世界株式（オール・カントリー）', amount: 3000000, asset_class: 'developed_stock', account_type: 'nisa_growth' },
    { ticker: 'eMAXIS Slim 国内株式', name: 'eMAXIS Slim 国内株式（TOPIX）', amount: 2000000, asset_class: 'domestic_stock', account_type: 'nisa_growth' },
    { ticker: 'eMAXIS Slim 先進国債券', name: 'eMAXIS Slim 先進国債券インデックス', amount: 1000000, asset_class: 'developed_bond', account_type: 'tokutei' },
  ]);
  const [assetClasses, setAssetClasses] = useState<AssetClass[]>([]);
  const [metrics, setMetrics] = useState<PortfolioMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{ ticker: string; name: string; asset_class: string }>>([]);
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    loadAssetClasses();
  }, []);

  const loadAssetClasses = async () => {
    try {
      const data = await portfolioApi.getAssetClasses();
      setAssetClasses(data);
    } catch (error) {
      console.error('Failed to load asset classes:', error);
    }
  };

  const analyzePortfolio = async () => {
    if (holdings.length === 0) return;
    
    setLoading(true);
    try {
      const data = await portfolioApi.analyzePortfolio(holdings);
      setMetrics(data);
    } catch (error) {
      console.error('Failed to analyze portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchSecurities = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const results = await portfolioApi.searchSecurities(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Failed to search securities:', error);
    }
  };

  const addHolding = (security: { ticker: string; name: string; asset_class: string }) => {
    const newHolding: PortfolioHolding = {
      ticker: security.ticker,
      name: security.name,
      amount: 0,
      asset_class: security.asset_class,
      account_type: 'tokutei',
    };
    setHoldings([...holdings, newHolding]);
    setShowSearch(false);
    setSearchQuery('');
    setSearchResults([]);
  };

  const updateHolding = (index: number, field: keyof PortfolioHolding, value: string | number) => {
    const updated = [...holdings];
    updated[index] = { ...updated[index], [field]: value };
    setHoldings(updated);
  };

  const removeHolding = (index: number) => {
    setHoldings(holdings.filter((_, i) => i !== index));
  };

  const totalAmount = holdings.reduce((sum, h) => sum + h.amount, 0);

  const allocationByClass = holdings.reduce((acc, h) => {
    const cls = h.asset_class;
    acc[cls] = (acc[cls] || 0) + h.amount;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">ポートフォリオ</h1>
        <p className="text-gray-600 mt-1">保有銘柄の管理と分析</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>保有銘柄</CardTitle>
                  <CardDescription>ポートフォリオに含まれる銘柄</CardDescription>
                </div>
                <Button onClick={() => setShowSearch(!showSearch)} size="sm">
                  <Plus className="h-4 w-4 mr-1" />
                  銘柄追加
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {showSearch && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <div className="flex gap-2 mb-4">
                    <Input
                      placeholder="銘柄名で検索..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && searchSecurities()}
                    />
                    <Button onClick={searchSecurities} size="sm">
                      <Search className="h-4 w-4" />
                    </Button>
                  </div>
                  {searchResults.length > 0 && (
                    <div className="space-y-2">
                      {searchResults.map((result) => (
                        <div
                          key={result.ticker}
                          className="flex items-center justify-between p-2 bg-white rounded border hover:border-blue-500 cursor-pointer"
                          onClick={() => addHolding(result)}
                        >
                          <div>
                            <div className="font-medium text-sm">{result.name}</div>
                            <div className="text-xs text-gray-500">{ASSET_CLASS_NAMES[result.asset_class] || result.asset_class}</div>
                          </div>
                          <Plus className="h-4 w-4 text-blue-600" />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-4">
                {holdings.map((holding, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="font-medium">{holding.name}</div>
                        <div className="text-sm text-gray-500 flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${ASSET_CLASS_COLORS[holding.asset_class] || 'bg-gray-400'}`}></span>
                          {ASSET_CLASS_NAMES[holding.asset_class] || holding.asset_class}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeHolding(index)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs">保有額（円）</Label>
                        <Input
                          type="number"
                          value={holding.amount}
                          onChange={(e) => updateHolding(index, 'amount', parseInt(e.target.value) || 0)}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">口座区分</Label>
                        <select
                          value={holding.account_type}
                          onChange={(e) => updateHolding(index, 'account_type', e.target.value)}
                          className="mt-1 w-full h-10 px-3 rounded-md border border-gray-200 text-sm"
                        >
                          <option value="tokutei">特定口座</option>
                          <option value="nisa_growth">NISA（成長投資枠）</option>
                          <option value="nisa_tsumitate">NISA（つみたて投資枠）</option>
                          <option value="ippan">一般口座</option>
                        </select>
                      </div>
                    </div>
                  </div>
                ))}

                {holdings.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    銘柄を追加してください
                  </div>
                )}
              </div>

              <div className="mt-6 pt-4 border-t">
                <div className="flex items-center justify-between mb-4">
                  <span className="font-medium">合計</span>
                  <span className="text-xl font-bold">{formatCurrency(totalAmount)}</span>
                </div>
                <Button onClick={analyzePortfolio} className="w-full" disabled={holdings.length === 0 || loading}>
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      分析中...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      ポートフォリオを分析
                    </span>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {metrics && (
            <Card>
              <CardHeader>
                <CardTitle>分析結果</CardTitle>
                <CardDescription>ポートフォリオの詳細分析</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="text-sm text-blue-600">期待リターン</div>
                    <div className="text-2xl font-bold text-blue-700">{(metrics.expected_return * 100).toFixed(2)}%</div>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <div className="text-sm text-red-600">リスク（標準偏差）</div>
                    <div className="text-2xl font-bold text-red-700">{(metrics.volatility * 100).toFixed(2)}%</div>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="text-sm text-green-600">シャープレシオ</div>
                    <div className="text-2xl font-bold text-green-700">{metrics.sharpe_ratio.toFixed(2)}</div>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <div className="text-sm text-purple-600">VaR (95%)</div>
                    <div className="text-2xl font-bold text-purple-700">{(metrics.var_95 * 100).toFixed(2)}%</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                資産配分
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(allocationByClass).map(([cls, amount]) => {
                  const percentage = totalAmount > 0 ? (amount / totalAmount) * 100 : 0;
                  return (
                    <div key={cls}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${ASSET_CLASS_COLORS[cls] || 'bg-gray-400'}`}></span>
                          <span>{ASSET_CLASS_NAMES[cls] || cls}</span>
                        </div>
                        <span className="font-medium">{percentage.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${ASSET_CLASS_COLORS[cls] || 'bg-gray-400'}`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>資産クラス情報</CardTitle>
              <CardDescription>期待リターンとリスク</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                {assetClasses.slice(0, 6).map((ac) => (
                  <div key={ac.id} className="flex items-center justify-between py-1 border-b last:border-0">
                    <span className="text-gray-600">{ac.name}</span>
                    <div className="text-right">
                      <span className="text-green-600">{(ac.expected_return * 100).toFixed(1)}%</span>
                      <span className="text-gray-400 mx-1">/</span>
                      <span className="text-red-600">{(ac.volatility * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
