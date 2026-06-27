import React, { useEffect, useState, useMemo } from 'react';
import { DollarSign, Lightbulb, Package, ShoppingCart, TrendingUp, Hash, Search, AlertCircle, RefreshCw } from 'lucide-react';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area,
} from 'recharts';
import dataService from '../../services/dataService';
import { useI18n } from '../../i18n';

const SCOPES = [
  { id: 'day',       labelKey: 'scope.day'       },
  { id: 'week',      labelKey: 'scope.week'      },
  { id: 'month',     labelKey: 'scope.month'     },
  { id: 'year',      labelKey: 'scope.year'      },
  { id: '5years',    labelKey: 'scope.5years'    },
  { id: 'beginning', labelKey: 'scope.beginning' },
];

const MONTHS_KEYS = ['month.jan','month.feb','month.mar','month.apr','month.may','month.jun','month.jul','month.aug','month.sep','month.oct','month.nov','month.dec'];

const formatDate = (dateStr, scope, t) => {
  const d = new Date(dateStr + 'T00:00:00');
  const m = t(MONTHS_KEYS[d.getMonth()]);
  const day = d.getDate();
  const y = d.getFullYear();
  if (scope === 'day')             return `${m} ${day}`;
  if (scope === 'week' || scope === 'beginning') return `${m} ${day}, ${y}`;
  if (scope === 'month')           return `${m} ${y}`;
  if (scope === 'year')            return `Q${Math.floor(d.getMonth() / 3) + 1} ${y}`;
  if (scope === '5years')          return `${y}`;
  return `${m} ${day}`;
};

const InfoCard = ({ icon, label, value, color }) => (
  <div className="surface" style={{ position: 'relative' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '500' }}>{label}</span>
      <div style={{ color }}>{icon}</div>
    </div>
    <div className="outfit" style={{ fontSize: '22px', fontWeight: '700', marginTop: '12px', wordBreak: 'break-word' }}>{value}</div>
  </div>
);

const Product = () => {
  const { t } = useI18n();
  const [products, setProducts]       = useState([]);
  const [searchName, setSearchName]   = useState('');
  const [searchId, setSearchId]       = useState('');
  const [selectedId, setSelectedId]   = useState(null);
  const [product, setProduct]         = useState(null);
  const [loadingProduct, setLoadingProduct] = useState(false);

  const [scope, setScope] = useState('month');
  const [salesData, setSalesData] = useState([]);
  const [loadingSales, setLoadingSales] = useState(false);

  const [horizon, setHorizon] = useState(30);
  const [forecastData, setForecastData] = useState(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastError, setForecastError] = useState(null);

  const [insight, setInsight] = useState(null);
  const [insightLoading, setInsightLoading] = useState(false);

  const [pageLoading, setPageLoading] = useState(true);

  const handleInsight = async () => {
    if (!selectedId) return;
    setInsightLoading(true);
    setInsight(null);
    try {
      const res = await dataService.getInsight(parseInt(selectedId), scope, 4);
      if (res && res.status === 'success') {
        setInsight(res);
      } else {
        setInsight({ status: 'error', message: res?.message || 'Failed to generate insights' });
      }
    } catch (err) {
      console.error('Insight failed:', err);
      setInsight({ status: 'error', message: err.message });
    } finally {
      setInsightLoading(false);
    }
  };

  const handleForecast = async () => {
    if (!selectedId) return;
    setForecastLoading(true);
    setForecastError(null);
    try {
      const res = await dataService.getForecast(parseInt(selectedId), horizon);
      if (res && res.forecast && res.forecast.length > 0) {
        setForecastData(res.forecast);
      } else if (res && res.status === 'no_data') {
        setForecastError('لا توجد بيانات مبيعات كافية للتوقع (no sales data for this product).');
      } else {
        setForecastError('تعذر إنشاء التوقعات - تحقق من اتصال الخادم (Forecast returned no data).');
      }
    } catch (err) {
      console.error('Forecast failed:', err);
      const msg = err.message || '';
      if (msg.includes('Network error') || msg.includes('Is the backend running')) {
        setForecastError('تعذر الاتصال بالخادم - تأكد من أن الخادم يعمل على المنفذ 8000 (Cannot reach server).');
      } else {
        setForecastError(msg || 'فشل في إنشاء التوقعات (Failed to generate forecast).');
      }
    } finally {
      setForecastLoading(false);
    }
  };

  useEffect(() => {
    const load = async () => {
      try {
        const res = await dataService.getProducts();
        setProducts(res || []);
      } catch (err) {
        console.error('Failed to load products:', err);
      } finally {
        setPageLoading(false);
      }
    };
    load();
  }, []);

  const filtered = useMemo(() => {
    let list = products;
    if (searchName.trim()) {
      const q = searchName.trim().toLowerCase();
      list = list.filter(p => p.name.toLowerCase().includes(q));
    }
    if (searchId.trim()) {
      const q = searchId.trim();
      list = list.filter(p => String(p.id).startsWith(q));
    }
    return list;
  }, [products, searchName, searchId]);

  useEffect(() => {
    if (!selectedId) return;
    setForecastData(null);
    setForecastError(null);
    setLoadingProduct(true);
    setLoadingSales(true);

    dataService.getProductById(parseInt(selectedId))
      .then(setProduct)
      .catch(err => { console.error(err); setProduct(null); })
      .finally(() => setLoadingProduct(false));

    dataService.getProductSales(parseInt(selectedId), scope)
      .then(res => {
        const sales = res?.sales || [];
        setSalesData(sales.map(s => ({
          name: formatDate(s.date, scope, t),
          sales: Math.round(s.quantity),
        })));
      })
      .catch(err => { console.error(err); setSalesData([]); })
      .finally(() => setLoadingSales(false));
  }, [selectedId, scope]);

  const totalSales = useMemo(() => {
    if (!salesData.length) return '---';
    return salesData.reduce((s, d) => s + d.sales, 0).toLocaleString();
  }, [salesData]);

  const totalRevenue = useMemo(() => {
    if (!product || !product.base_price) return '---';
    const count = salesData.reduce((s, d) => s + d.sales, 0);
    return `$${(count * product.base_price).toLocaleString()}`;
  }, [product, salesData]);

  const chartData = useMemo(() => {
    if (!forecastData || forecastData.length === 0) return salesData;
    const data = salesData.map(s => ({ name: s.name, sales: s.sales }));
    forecastData.forEach((val, i) => {
      data.push({ name: `F${i + 1}`, forecast: Math.round(val) });
    });
    return data;
  }, [salesData, forecastData]);

  if (pageLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px' }}>
        <RefreshCw size={24} color="var(--accent-color)" className="spin" />
      </div>
    );
  }

  return (
    <div>
      <div className="surface">
        {/* ── Header & Search ── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
          <h3 className="outfit" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Package size={20} color="var(--accent-color)" /> {t('product.title')}
          </h3>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div className="surface" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '8px', borderRadius: '10px', border: '1px solid var(--border-color)', background: 'var(--surface-hover)' }}>
              <Search size={14} color="var(--text-secondary)" />
              <input
                type="text"
                placeholder={t('product.search_name')}
                value={searchName}
                onChange={e => setSearchName(e.target.value)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', width: '140px', fontSize: '12px', fontFamily: 'inherit' }}
              />
            </div>
            <div className="surface" style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '8px', borderRadius: '10px', border: '1px solid var(--border-color)', background: 'var(--surface-hover)' }}>
              <Hash size={14} color="var(--text-secondary)" />
              <input
                type="text"
                placeholder={t('product.search_id')}
                value={searchId}
                onChange={e => setSearchId(e.target.value)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', width: '100px', fontSize: '12px', fontFamily: 'inherit' }}
              />
            </div>
            <select
              value={selectedId || ''}
              onChange={e => setSelectedId(e.target.value)}
              style={{
                padding: '7px 14px', fontSize: '12px', fontFamily: 'inherit',
                fontWeight: '500', borderRadius: '8px', border: '1px solid var(--border-color)',
                cursor: 'pointer', background: 'var(--surface-hover)', color: 'var(--text-primary)',
                outline: 'none', minWidth: '180px',
              }}
            >
              <option value="">{t('product.select_default')}</option>
              {filtered.map(p => (
                <option key={p.id} value={p.id}>#{p.id} — {p.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* ── Product Info Cards ── */}
        {!selectedId && !loadingProduct && (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', padding: '48px 0' }}>
            <Search size={20} style={{ marginInlineEnd: '8px' }} /> {t('product.select_prompt')}
          </div>
        )}

        {selectedId && loadingProduct && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0' }}>
            <RefreshCw size={20} color="var(--accent-color)" className="spin" />
          </div>
        )}

        {selectedId && !loadingProduct && product && (
          <div className="card-grid" style={{ marginBottom: '28px' }}>
            <InfoCard icon={<Package size={20} />} label={t('product.name_label')} value={product.name} color="var(--accent-color)" />
            <InfoCard icon={<Hash size={20} />} label={t('product.id_label')} value={`#${product.id}`} color="#3b82f6" />
            <InfoCard icon={<DollarSign size={20} />} label={t('product.price_label')} value={`$${product.base_price?.toFixed(2) || '---'}`} color="#10b981" />
            <InfoCard icon={<ShoppingCart size={20} />} label={t('product.stock_label')} value={product.current_stock != null ? t('product.stock_units', { count: product.current_stock }) : '---'} color="#f59e0b" />
            <InfoCard icon={<TrendingUp size={20} />} label={t('product.sales_qty_label')} value={totalSales} color="#a855f7" />
            <InfoCard icon={<DollarSign size={20} />} label={t('product.revenue_label')} value={totalRevenue} color="#ec4899" />
          </div>
        )}

        {selectedId && !loadingProduct && !product && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0', color: 'var(--text-secondary)' }}>
            <AlertCircle size={20} style={{ marginInlineEnd: '8px' }} /> {t('product.unavailable')}
          </div>
        )}

        {/* ── Sales Timeline Chart ── */}
        {selectedId && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h4 className="outfit" style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={18} color="var(--accent-color)" /> {t('product.sales_timeline')}
              </h4>
              <div style={{ display: 'flex', gap: '4px', background: 'var(--surface-hover)', padding: '4px', borderRadius: '10px' }}>
                {SCOPES.map(({ id, labelKey }) => (
                  <button
                    key={id}
                    onClick={() => setScope(id)}
                    style={{
                      padding: '5px 12px', fontSize: '11px', fontFamily: 'inherit',
                      fontWeight: scope === id ? '600' : '400',
                      borderRadius: '7px', border: 'none', cursor: 'pointer',
                      transition: 'all 0.18s ease',
                      background: scope === id ? 'var(--accent-color)' : 'transparent',
                      color:      scope === id ? '#0f172a' : 'var(--text-secondary)',
                    }}
                  >
                    {t(labelKey)}
                  </button>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="number"
                  min={1}
                  max={365}
                  value={horizon}
                  onChange={e => setHorizon(parseInt(e.target.value) || 1)}
                  title={t('product.forecast_horizon')}
                  style={{
                    width: '52px', padding: '5px 8px', fontSize: '11px', fontFamily: 'inherit',
                    borderRadius: '7px', border: '1px solid var(--border-color)',
                    background: 'var(--bg-color)', color: 'var(--text-primary)',
                    outline: 'none', textAlign: 'center',
                  }}
                />
                <button
                  onClick={handleForecast}
                  disabled={forecastLoading || !selectedId}
                  className="btn btn-primary"
                  style={{
                    padding: '5px 14px', fontSize: '11px', fontWeight: '600',
                    display: 'flex', gap: '6px', alignItems: 'center',
                    borderRadius: '8px', height: '32px',
                  }}
                >
                  {forecastLoading ? <RefreshCw size={14} className="spin" /> : <TrendingUp size={14} />}
                  {t('product.forecast')}
                </button>
              </div>
            </div>

            {loadingSales && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '250px' }}>
                <RefreshCw size={20} color="var(--accent-color)" className="spin" />
              </div>
            )}

            {!loadingSales && salesData.length === 0 && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '250px', color: 'var(--text-secondary)' }}>
                <AlertCircle size={20} style={{ marginInlineEnd: '8px' }} /> {t('product.no_sales')}
              </div>
            )}

            {!loadingSales && chartData.length > 0 && (
              <div style={{ height: '280px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorProductSalesTimeline" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="var(--accent-color)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="var(--accent-color)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                    <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" angle={-20} textAnchor="end" height={60} />
                    <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px', color: 'var(--text-primary)', fontSize: '12px' }} />
                    <Area type="monotone" dataKey="sales" name={t('chart.sales')} stroke="var(--accent-color)" strokeWidth={3} fillOpacity={1} fill="url(#colorProductSalesTimeline)" />
                    {forecastData && forecastData.length > 0 && (
                      <Area type="monotone" dataKey="forecast" name={t('chart.forecast')} stroke="#f59e0b" strokeDasharray="5 5" strokeWidth={3} fillOpacity={0.05} fill="#f59e0b" dot={{ r: 3, fill: '#f59e0b' }} connectNulls />
                    )}
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
            {forecastError && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', marginTop: '8px', borderRadius: '8px', background: 'rgba(239,68,68,0.08)', color: '#ef4444', fontSize: '12px' }}>
                <AlertCircle size={14} /> {forecastError}
              </div>
            )}
          </div>
        )}

        {/* ── Insights Section ── */}
        {selectedId && !loadingProduct && (
          <div style={{ marginTop: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h4 className="outfit" style={{ fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Lightbulb size={18} color="var(--accent-color)" /> {t('insight.title')}
              </h4>
              <button
                onClick={handleInsight}
                disabled={insightLoading || !selectedId}
                className="btn btn-primary"
                style={{
                  padding: '5px 14px', fontSize: '11px', fontWeight: '600',
                  display: 'flex', gap: '6px', alignItems: 'center',
                  borderRadius: '8px', height: '32px',
                }}
              >
                {insightLoading ? <RefreshCw size={14} className="spin" /> : <Lightbulb size={14} />}
                {insight ? t('insight.regenerate') : t('insight.generate')}
              </button>
            </div>

            {/* Loading state */}
            {insightLoading && (
              <div className="surface" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <RefreshCw size={20} color="var(--accent-color)" className="spin" style={{ marginBottom: '8px' }} />
                <div style={{ fontSize: '13px' }}>{t('insight.generating')}</div>
              </div>
            )}

            {/* LLM unavailable → rule-based fallback badge */}
            {insight && insight.method === 'fallback_rule' && !insightLoading && (
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '8px', fontStyle: 'italic' }}>
                {t('insight.fallback')}
              </div>
            )}

            {/* Insight card */}
            {insight && insight.status === 'success' && !insightLoading && (
              <div className="surface" style={{ padding: '20px' }}>
                {/* Recommendation */}
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '500', marginBottom: '4px' }}>{t('insight.recommendation')}</div>
                  <div style={{ fontSize: '16px', fontWeight: '600', color: insight.reorder_in_days <= 3 ? '#ef4444' : 'var(--text-primary)', lineHeight: '1.5' }}>
                    {insight.reorder_recommendation}
                  </div>
                </div>

                {/* Metrics row */}
                <div className="card-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', marginBottom: '16px' }}>
                  <div className="surface" style={{ padding: '12px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: '500' }}>{t('insight.order_qty')}</div>
                    <div style={{ fontSize: '20px', fontWeight: '700', marginTop: '4px' }}>{insight.order_quantity > 0 ? `${insight.order_quantity} ${t('insight.units')}` : '—'}</div>
                  </div>
                  <div className="surface" style={{ padding: '12px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: '500' }}>{t('insight.reorder_in')}</div>
                    <div style={{ fontSize: '20px', fontWeight: '700', marginTop: '4px', color: insight.reorder_in_days <= 3 ? '#ef4444' : insight.reorder_in_days <= 7 ? '#f59e0b' : 'var(--text-primary)' }}>
                      {insight.reorder_in_days > 0 ? `${insight.reorder_in_days} ${t('insight.days')}` : 'Today'}
                    </div>
                  </div>
                  <div className="surface" style={{ padding: '12px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: '500' }}>{t('insight.stock_out')}</div>
                    <div style={{ fontSize: '20px', fontWeight: '700', marginTop: '4px', color: insight.stock_out_in_days != null && insight.stock_out_in_days <= 14 ? '#ef4444' : 'var(--text-primary)' }}>
                      {insight.stock_out_in_days != null ? `${insight.stock_out_in_days} ${t('insight.days')}` : '—'}
                    </div>
                  </div>
                  <div className="surface" style={{ padding: '12px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: '500' }}>{t('insight.confidence')}</div>
                    <div style={{ fontSize: '20px', fontWeight: '700', marginTop: '4px', textTransform: 'capitalize', color: insight.confidence === 'high' ? '#10b981' : insight.confidence === 'medium' ? '#f59e0b' : '#ef4444' }}>
                      {insight.confidence}
                    </div>
                  </div>
                </div>

                {/* Key Factors */}
                {insight.key_factors && insight.key_factors.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '500', marginBottom: '6px' }}>{t('insight.key_factors')}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {insight.key_factors.map((f, i) => (
                        <div key={i} style={{ fontSize: '12px', padding: '4px 8px', background: 'var(--surface-hover)', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ color: '#10b981' }}>◆</span> {f}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Risk Factors */}
                {insight.risk_factors && insight.risk_factors.length > 0 && (
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '500', marginBottom: '6px' }}>{t('insight.risk_factors')}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {insight.risk_factors.map((f, i) => (
                        <div key={i} style={{ fontSize: '12px', padding: '4px 8px', background: 'var(--surface-hover)', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ color: '#ef4444' }}>⚠</span> {f}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Error state */}
            {insight && insight.status === 'error' && !insightLoading && (
              <div className="surface" style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <AlertCircle size={20} style={{ marginBottom: '8px', margin: '0 auto 8px', display: 'block' }} />
                <div style={{ fontSize: '13px' }}>{insight.message || 'Failed to generate insight'}</div>
              </div>
            )}

            {/* No data state */}
            {insight && insight.status === 'no_data' && !insightLoading && (
              <div className="surface" style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <AlertCircle size={20} style={{ marginBottom: '8px', margin: '0 auto 8px', display: 'block' }} />
                <div style={{ fontSize: '13px' }}>{insight.message || t('insight.no_data')}</div>
              </div>
            )}
          </div>
        )}
      </div>
      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default Product;
