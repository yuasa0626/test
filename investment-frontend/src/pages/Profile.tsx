import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { User, Users, DollarSign, Home, Car, GraduationCap, Plus, Trash2, Save } from 'lucide-react';
import type { FamilyMember, Liability } from '@/types';

export default function Profile() {
  const [profile, setProfile] = useState({
    age: 35,
    occupation: '会社員',
    annual_income: 6000000,
    monthly_expenses: 250000,
    monthly_investment: 50000,
    savings: 5000000,
    emergency_fund: 1000000,
  });

  const [spouse, setSpouse] = useState<{ age: number; occupation: string } | null>(null);
  const [children, setChildren] = useState<FamilyMember[]>([]);
  const [liabilities, setLiabilities] = useState<Liability[]>([]);
  const [saved, setSaved] = useState(false);

  const addSpouse = () => {
    setSpouse({ age: 33, occupation: '会社員' });
  };

  const removeSpouse = () => {
    setSpouse(null);
  };

  const addChild = () => {
    setChildren([...children, { name: `子供${children.length + 1}`, age: 0 }]);
  };

  const updateChild = (index: number, field: keyof FamilyMember, value: string | number) => {
    const updated = [...children];
    updated[index] = { ...updated[index], [field]: value };
    setChildren(updated);
  };

  const removeChild = (index: number) => {
    setChildren(children.filter((_, i) => i !== index));
  };

  const addLiability = () => {
    setLiabilities([
      ...liabilities,
      { type: 'housing', name: '住宅ローン', balance: 0, monthly_payment: 0, interest_rate: 0.01, remaining_years: 30 },
    ]);
  };

  const updateLiability = (index: number, field: keyof Liability, value: string | number) => {
    const updated = [...liabilities];
    updated[index] = { ...updated[index], [field]: value };
    setLiabilities(updated);
  };

  const removeLiability = (index: number) => {
    setLiabilities(liabilities.filter((_, i) => i !== index));
  };

  const saveProfile = () => {
    localStorage.setItem('userProfile', JSON.stringify({
      profile,
      spouse,
      children,
      liabilities,
    }));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">プロファイル</h1>
          <p className="text-gray-600 mt-1">ユーザー情報とライフプラン設定</p>
        </div>
        <Button onClick={saveProfile} className="flex items-center gap-2">
          <Save className="h-4 w-4" />
          {saved ? '保存しました' : '保存'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              本人情報
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>年齢</Label>
                <Input
                  type="number"
                  value={profile.age}
                  onChange={(e) => setProfile({ ...profile, age: parseInt(e.target.value) || 0 })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label>職業</Label>
                <select
                  value={profile.occupation}
                  onChange={(e) => setProfile({ ...profile, occupation: e.target.value })}
                  className="mt-1 w-full h-10 px-3 rounded-md border border-gray-200 text-sm"
                >
                  <option value="会社員">会社員</option>
                  <option value="公務員">公務員</option>
                  <option value="自営業">自営業</option>
                  <option value="パート・アルバイト">パート・アルバイト</option>
                  <option value="専業主婦・主夫">専業主婦・主夫</option>
                  <option value="年金受給者">年金受給者</option>
                  <option value="その他">その他</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              家族情報
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {spouse ? (
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-medium">配偶者</span>
                  <Button variant="ghost" size="sm" onClick={removeSpouse} className="text-red-600">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs">年齢</Label>
                    <Input
                      type="number"
                      value={spouse.age}
                      onChange={(e) => setSpouse({ ...spouse, age: parseInt(e.target.value) || 0 })}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">職業</Label>
                    <select
                      value={spouse.occupation}
                      onChange={(e) => setSpouse({ ...spouse, occupation: e.target.value })}
                      className="mt-1 w-full h-10 px-3 rounded-md border border-gray-200 text-sm"
                    >
                      <option value="会社員">会社員</option>
                      <option value="公務員">公務員</option>
                      <option value="自営業">自営業</option>
                      <option value="パート・アルバイト">パート・アルバイト</option>
                      <option value="専業主婦・主夫">専業主婦・主夫</option>
                      <option value="その他">その他</option>
                    </select>
                  </div>
                </div>
              </div>
            ) : (
              <Button variant="outline" onClick={addSpouse} className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                配偶者を追加
              </Button>
            )}

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-medium flex items-center gap-2">
                  <GraduationCap className="h-4 w-4" />
                  子供
                </span>
                <Button variant="outline" size="sm" onClick={addChild}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {children.map((child, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium">{child.name}</span>
                    <Button variant="ghost" size="sm" onClick={() => removeChild(index)} className="text-red-600">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs">名前</Label>
                      <Input
                        value={child.name}
                        onChange={(e) => updateChild(index, 'name', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">年齢</Label>
                      <Input
                        type="number"
                        value={child.age}
                        onChange={(e) => updateChild(index, 'age', parseInt(e.target.value) || 0)}
                        className="mt-1"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5" />
              キャッシュフロー
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>年収（円）</Label>
              <Input
                type="number"
                value={profile.annual_income}
                onChange={(e) => setProfile({ ...profile, annual_income: parseInt(e.target.value) || 0 })}
                className="mt-1"
              />
            </div>
            <div>
              <Label>月間支出（円）</Label>
              <Input
                type="number"
                value={profile.monthly_expenses}
                onChange={(e) => setProfile({ ...profile, monthly_expenses: parseInt(e.target.value) || 0 })}
                className="mt-1"
              />
            </div>
            <div>
              <Label>月間投資額（円）</Label>
              <Input
                type="number"
                value={profile.monthly_investment}
                onChange={(e) => setProfile({ ...profile, monthly_investment: parseInt(e.target.value) || 0 })}
                className="mt-1"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Home className="h-5 w-5" />
              資産
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>預貯金（円）</Label>
              <Input
                type="number"
                value={profile.savings}
                onChange={(e) => setProfile({ ...profile, savings: parseInt(e.target.value) || 0 })}
                className="mt-1"
              />
            </div>
            <div>
              <Label>緊急予備資金（円）</Label>
              <Input
                type="number"
                value={profile.emergency_fund}
                onChange={(e) => setProfile({ ...profile, emergency_fund: parseInt(e.target.value) || 0 })}
                className="mt-1"
              />
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Car className="h-5 w-5" />
                  負債
                </CardTitle>
                <CardDescription>住宅ローン、自動車ローンなど</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={addLiability}>
                <Plus className="h-4 w-4 mr-1" />
                追加
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {liabilities.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                負債を追加してください
              </div>
            ) : (
              <div className="space-y-4">
                {liabilities.map((liability, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <select
                        value={liability.type}
                        onChange={(e) => updateLiability(index, 'type', e.target.value)}
                        className="h-10 px-3 rounded-md border border-gray-200 text-sm"
                      >
                        <option value="housing">住宅ローン</option>
                        <option value="car">自動車ローン</option>
                        <option value="education">教育ローン</option>
                        <option value="other">その他</option>
                      </select>
                      <Button variant="ghost" size="sm" onClick={() => removeLiability(index)} className="text-red-600">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <Label className="text-xs">名称</Label>
                        <Input
                          value={liability.name}
                          onChange={(e) => updateLiability(index, 'name', e.target.value)}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">残高（円）</Label>
                        <Input
                          type="number"
                          value={liability.balance}
                          onChange={(e) => updateLiability(index, 'balance', parseInt(e.target.value) || 0)}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">月額返済（円）</Label>
                        <Input
                          type="number"
                          value={liability.monthly_payment}
                          onChange={(e) => updateLiability(index, 'monthly_payment', parseInt(e.target.value) || 0)}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">残り年数</Label>
                        <Input
                          type="number"
                          value={liability.remaining_years}
                          onChange={(e) => updateLiability(index, 'remaining_years', parseInt(e.target.value) || 0)}
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
