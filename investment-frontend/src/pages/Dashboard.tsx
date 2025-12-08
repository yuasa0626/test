import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, DollarSign, PieChart, AlertTriangle, Target } from 'lucide-react';

interface DashboardMetrics {
  totalAssets: number;
  expectedReturn: number;
  portfolioRisk: number;
  sharpeRatio: number;
}

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

function MetricCard({ 
  title, 
  value, 
  description, 
  icon: Icon, 
  trend 
}: { 
  title: string; 
  value: string; 
  description?: string; 
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'neutral';
}) {
  const trendColor = trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600';
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        <Icon className={`h-5 w-5 ${trendColor}`} />
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${trendColor}`}>{value}</div>
        {description && (
          <p className="text-xs text-gray-500 mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalAssets: 10000000,
    expectedReturn: 5.2,
    portfolioRisk: 12.5,
    sharpeRatio: 0.42,
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    setTimeout(() => {
      setMetrics({
        totalAssets: 10000000,
        expectedReturn: 5.2,
        portfolioRisk: 12.5,
        sharpeRatio: 0.42,
      });
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">ダッシュボード</h1>
        <p className="text-gray-600 mt-1">ポートフォリオの概要と主要指標</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="総資産額"
          value={formatCurrency(metrics.totalAssets)}
          description="現在の評価額"
          icon={DollarSign}
          trend="neutral"
        />
        <MetricCard
          title="期待リターン"
          value={`${metrics.expectedReturn.toFixed(1)}%`}
          description="年率換算"
          icon={TrendingUp}
          trend="up"
        />
        <MetricCard
          title="ポートフォリオリスク"
          value={`${metrics.portfolioRisk.toFixed(1)}%`}
          description="標準偏差（年率）"
          icon={AlertTriangle}
          trend="neutral"
        />
        <MetricCard
          title="シャープレシオ"
          value={metrics.sharpeRatio.toFixed(2)}
          description="リスク調整後リターン"
          icon={Target}
          trend={metrics.sharpeRatio > 0.5 ? 'up' : 'neutral'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              資産配分
            </CardTitle>
            <CardDescription>
              現在のポートフォリオ構成
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm">国内株式</span>
                </div>
                <span className="text-sm font-medium">30%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-sm">先進国株式</span>
                </div>
                <span className="text-sm font-medium">40%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <span className="text-sm">新興国株式</span>
                </div>
                <span className="text-sm font-medium">10%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <span className="text-sm">国内債券</span>
                </div>
                <span className="text-sm font-medium">15%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span className="text-sm">先進国債券</span>
                </div>
                <span className="text-sm font-medium">5%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5" />
              リスク指標
            </CardTitle>
            <CardDescription>
              ポートフォリオのリスク分析
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">VaR (95%)</span>
                <span className="text-sm font-medium text-red-600">-8.2%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">CVaR (95%)</span>
                <span className="text-sm font-medium text-red-600">-12.5%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">最大ドローダウン</span>
                <span className="text-sm font-medium text-red-600">-25.3%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">ソルティノレシオ</span>
                <span className="text-sm font-medium">0.58</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">情報レシオ</span>
                <span className="text-sm font-medium">0.35</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>クイックアクション</CardTitle>
          <CardDescription>
            よく使う機能へのショートカット
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="/portfolio"
              className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <PieChart className="h-6 w-6 text-blue-600" />
              <div>
                <div className="font-medium">ポートフォリオ分析</div>
                <div className="text-sm text-gray-500">保有銘柄の詳細分析</div>
              </div>
            </a>
            <a
              href="/simulation"
              className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-green-500 hover:bg-green-50 transition-colors"
            >
              <TrendingUp className="h-6 w-6 text-green-600" />
              <div>
                <div className="font-medium">シミュレーション</div>
                <div className="text-sm text-gray-500">将来予測を実行</div>
              </div>
            </a>
            <a
              href="/stress-test"
              className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-red-500 hover:bg-red-50 transition-colors"
            >
              <AlertTriangle className="h-6 w-6 text-red-600" />
              <div>
                <div className="font-medium">ストレステスト</div>
                <div className="text-sm text-gray-500">危機シナリオ分析</div>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
