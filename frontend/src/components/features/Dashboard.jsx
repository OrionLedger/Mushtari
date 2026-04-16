import React, { useEffect, useState } from 'react';
import { Wifi, WifiOff, DollarSign, Percent, MousePointerClick, PieChart } from 'lucide-react';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, PieChart as RechartsPie, Pie, Cell,
} from 'recharts';
import { aiService } from '../../services/api';

// ─── Scope Data for Demand Chart ───────────────────────────────────────────────
const SCOPE_DATA = {
  day:       [
    { name: '00:00', sales: 800,  forecast: 750  },
    { name: '04:00', sales: 400,  forecast: 420  },
    { name: '08:00', sales: 1200, forecast: 1100 },
    { name: '12:00', sales: 2100, forecast: 1950 },
    { name: '16:00', sales: 2800, forecast: 2600 },
    { name: '20:00', sales: 1900, forecast: 2000 },
    { name: '23:59', sales: 950,  forecast: 1000 },
  ],
  week:      [
    { name: 'Mon', sales: 4000, forecast: 2400 },
    { name: 'Tue', sales: 3000, forecast: 3100 },
    { name: 'Wed', sales: 2000, forecast: 2600 },
    { name: 'Thu', sales: 2780, forecast: 2900 },
    { name: 'Fri', sales: 1890, forecast: 2200 },
    { name: 'Sat', sales: 2390, forecast: 2700 },
    { name: 'Sun', sales: 3490, forecast: 3200 },
  ],
  month:     [
    { name: 'W1', sales: 14200, forecast: 13000 },
    { name: 'W2', sales: 18500, forecast: 17200 },
    { name: 'W3', sales: 16800, forecast: 17900 },
    { name: 'W4', sales: 21400, forecast: 20100 },
  ],
  year:      [
    { name: 'Jan', sales: 52000, forecast: 48000 },
    { name: 'Feb', sales: 47000, forecast: 50000 },
    { name: 'Mar', sales: 61000, forecast: 58000 },
    { name: 'Apr', sales: 55000, forecast: 57000 },
    { name: 'May', sales: 67000, forecast: 63000 },
    { name: 'Jun', sales: 71000, forecast: 69000 },
    { name: 'Jul', sales: 80000, forecast: 75000 },
    { name: 'Aug', sales: 76000, forecast: 77000 },
    { name: 'Sep', sales: 65000, forecast: 68000 },
    { name: 'Oct', sales: 72000, forecast: 70000 },
    { name: 'Nov', sales: 84000, forecast: 80000 },
    { name: 'Dec', sales: 91000, forecast: 88000 },
  ],
  '5years':  [
    { name: '2020', sales: 310000, forecast: 290000 },
    { name: '2021', sales: 420000, forecast: 390000 },
    { name: '2022', sales: 580000, forecast: 540000 },
    { name: '2023', sales: 720000, forecast: 690000 },
    { name: '2024', sales: 890000, forecast: 860000 },
  ],
  beginning: [
    { name: '2018', sales: 120000, forecast: 100000 },
    { name: '2019', sales: 195000, forecast: 180000 },
    { name: '2020', sales: 310000, forecast: 290000 },
    { name: '2021', sales: 420000, forecast: 390000 },
    { name: '2022', sales: 580000, forecast: 540000 },
    { name: '2023', sales: 720000, forecast: 690000 },
    { name: '2024', sales: 890000, forecast: 860000 },
  ],
};

const SCOPES = [
  { id: 'day',       label: 'Day'       },
  { id: 'week',      label: 'Week'      },
  { id: 'month',     label: 'Month'     },
  { id: 'year',      label: 'Year'      },
  { id: '5years',    label: '5 Years'   },
  { id: 'beginning', label: 'Beginning' },
];

// ─── Revenue & Users mock data ──────────────────────────────────────────────────
const revenueData = {
  product: [
    { name: 'Product A', value: 32400 },
    { name: 'Product B', value: 21000 },
    { name: 'Product C', value: 17800 },
    { name: 'Product D', value: 9300  },
    { name: 'Product E', value: 4000  },
  ],
  country: [
    { name: 'Lebanon', value: 28000 },
    { name: 'UAE',     value: 22500 },
    { name: 'KSA',     value: 18000 },
    { name: 'Egypt',   value: 10500 },
    { name: 'Jordan',  value: 5500  },
  ],
  channel: [
    { name: 'Ads',     value: 49200 },
    { name: 'Organic', value: 35300 },
  ],
};

const usersData = {
  device: [
    { name: 'Mobile',  value: 58, color: '#2dd4bf' },
    { name: 'Desktop', value: 32, color: '#a855f7' },
    { name: 'Tablet',  value: 10, color: '#f59e0b' },
  ],
  source: [
    { name: 'Google', value: 41, color: '#3b82f6' },
    { name: 'Direct', value: 27, color: '#10b981' },
    { name: 'Social', value: 20, color: '#ec4899' },
    { name: 'Email',  value: 12, color: '#f59e0b' },
  ],
};

const BAR_COLOR = '#2dd4bf';

// ─── Sub-components ─────────────────────────────────────────────────────────────
const DemandChart = () => {
  const [chartScope, setChartScope] = useState('week');
  const chartData = SCOPE_DATA[chartScope];

  return (
    <div className="surface" style={{ marginTop: '32px', height: '400px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h3 className="outfit">Demand Insights</h3>
        <div style={{ display: 'flex', gap: '4px', background: 'var(--surface-hover)', padding: '4px', borderRadius: '10px' }}>
          {SCOPES.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setChartScope(id)}
              style={{
                padding: '6px 14px', fontSize: '12px', fontFamily: 'inherit',
                fontWeight: chartScope === id ? '600' : '400',
                borderRadius: '7px', border: 'none', cursor: 'pointer',
                transition: 'all 0.18s ease',
                background: chartScope === id ? 'var(--accent-color)' : 'transparent',
                color:      chartScope === id ? '#0f172a' : 'var(--text-secondary)',
                boxShadow:  chartScope === id ? '0 2px 8px rgba(45,212,191,0.25)' : 'none',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div style={{ flex: 1 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="var(--accent-color)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="var(--accent-color)" stopOpacity={0}   />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
            <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px', color: 'var(--text-primary)' }} />
            <Area type="monotone" dataKey="sales"    name="Historical Sales" stroke="var(--accent-color)"    strokeWidth={3} fillOpacity={1} fill="url(#colorSales)" />
            <Area type="monotone" dataKey="forecast" name="Forecast"         stroke="var(--text-secondary)" strokeDasharray="5 5" strokeWidth={2} fillOpacity={0} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// ─── Main Dashboard ──────────────────────────────────────────────────────────────
const Dashboard = () => {
  const [apiStatus, setApiStatus]   = useState(null);
  const [revenueTab, setRevenueTab] = useState('product');
  const [usersTab, setUsersTab]     = useState('device');
  const [alerts, setAlerts]         = useState([
    { type: 'critical', icon: '🔴', title: 'Sudden Drop in Sales',               desc: 'Product Alpha revenue dropped 34% compared to last week. Immediate review recommended.',             time: '2 min ago',   color: '#ef4444', bg: '#ef444412', border: '#ef444430' },
    { type: 'warning',  icon: '🟡', title: 'Increased Customer Acquisition Cost', desc: 'CAC rose from $4.20 to $7.80 over the past 3 days across Paid Ads channels.',                      time: '18 min ago',  color: '#f59e0b', bg: '#f59e0b12', border: '#f59e0b30' },
    { type: 'warning',  icon: '🟡', title: 'Drop in Conversion Rate',             desc: 'Checkout conversion fell from 3.2% to 1.9% — potential UX friction or pricing issue.',             time: '1 hour ago',  color: '#f59e0b', bg: '#f59e0b12', border: '#f59e0b30' },
    { type: 'info',     icon: '🔵', title: 'Forecast Model Drift Detected',       desc: 'ARIMA model predictions deviate >15% from actuals. Consider retraining with latest data.',         time: '3 hours ago', color: '#3b82f6', bg: '#3b82f612', border: '#3b82f630' },
    { type: 'info',     icon: '🔵', title: 'ETL Pipeline Delay',                  desc: 'Cassandra extraction job took 4.2× longer than average. Monitor for data lag.',                    time: '5 hours ago', color: '#3b82f6', bg: '#3b82f612', border: '#3b82f630' },
  ]);

  const stats = [
    { label: 'Revenue / Sales',  value: '$84,500', icon: <DollarSign size={20} />,      color: '#10b981' },
    { label: 'Growth %',         value: '18.5%',   icon: <Percent size={20} />,          color: '#3b82f6' },
    { label: 'Conversion Rate',  value: '3.2%',    icon: <MousePointerClick size={20} />, color: '#f59e0b' },
    { label: 'Profit / Margin',  value: '26.4%',   icon: <PieChart size={20} />,         color: '#a855f7' },
  ];

  useEffect(() => {
    aiService.getHealth()
      .then(() => setApiStatus('ok'))
      .catch(() => setApiStatus('error'));
  }, []);

  const TabBar = ({ tabs, active, onSelect }) => (
    <div style={{ display: 'flex', gap: '4px', background: 'var(--surface-hover)', padding: '4px', borderRadius: '8px' }}>
      {tabs.map(t => (
        <button key={t} onClick={() => onSelect(t)}
          style={{
            padding: '5px 12px', fontSize: '12px', borderRadius: '6px', border: 'none',
            cursor: 'pointer', textTransform: 'capitalize', fontFamily: 'inherit',
            fontWeight: active === t ? '600' : '400',
            background: active === t ? 'var(--accent-color)' : 'transparent',
            color:      active === t ? '#0f172a' : 'var(--text-secondary)',
          }}
        >{t}</button>
      ))}
    </div>
  );

  return (
    <div className="dashboard">

      {/* ── API Status ── */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
        {apiStatus === null && (
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)', padding: '6px 14px', borderRadius: '20px', background: 'var(--surface-hover)' }}>
            Checking API connection...
          </span>
        )}
        {apiStatus === 'ok' && (
          <span style={{ fontSize: '13px', color: '#10b981', padding: '6px 14px', borderRadius: '20px', background: '#10b98120', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Wifi size={14} /> Backend Connected
          </span>
        )}
        {apiStatus === 'error' && (
          <span style={{ fontSize: '13px', color: '#f59e0b', padding: '6px 14px', borderRadius: '20px', background: '#f59e0b20', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <WifiOff size={14} /> Backend Offline — Showing Mock Data
          </span>
        )}
      </div>

      {/* ── KPI Cards ── */}
      <div className="card-grid">
        {stats.map((stat, i) => (
          <div key={i} className="surface">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>{stat.label}</span>
              <div style={{ color: stat.color }}>{stat.icon}</div>
            </div>
            <div className="outfit" style={{ fontSize: '32px', fontWeight: '700', marginTop: '12px' }}>{stat.value}</div>
            <div style={{ color: '#10b981', fontSize: '12px', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>↑ 12%</span>
              <span style={{ color: 'var(--text-secondary)' }}>since last month</span>
            </div>
          </div>
        ))}
      </div>

      {/* ── Demand Chart ── */}
      <DemandChart />

      {/* ── Revenue By & Users By ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>

        {/* Revenue By */}
        <div className="surface" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 className="outfit">Revenue By</h3>
            <TabBar tabs={['product', 'country', 'channel']} active={revenueTab} onSelect={setRevenueTab} />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={revenueData[revenueTab]} layout="vertical" margin={{ left: 0, right: 20 }}>
              <XAxis type="number" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
              <YAxis type="category" dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} width={72} />
              <Tooltip formatter={v => [`$${v.toLocaleString()}`, 'Revenue']} contentStyle={{ backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '8px', fontSize: '13px' }} />
              <Bar dataKey="value" fill={BAR_COLOR} radius={[0, 6, 6, 0]} barSize={18} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Users By */}
        <div className="surface" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 className="outfit">Users By</h3>
            <TabBar tabs={['device', 'source']} active={usersTab} onSelect={setUsersTab} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <ResponsiveContainer width={180} height={200}>
              <RechartsPie>
                <Pie data={usersData[usersTab]} cx="50%" cy="50%" innerRadius={52} outerRadius={78} paddingAngle={3} dataKey="value">
                  {usersData[usersTab].map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={v => [`${v}%`, '']} contentStyle={{ backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '8px', fontSize: '13px' }} />
              </RechartsPie>
            </ResponsiveContainer>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
              {usersData[usersTab].map((entry, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: entry.color, flexShrink: 0 }} />
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{entry.name}</span>
                  </div>
                  <span style={{ fontSize: '13px', fontWeight: '600' }}>{entry.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Top / Worst Products ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
        {/* Top 5 Products */}
        <div className="surface">
          <h3 className="outfit" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#10b981' }}>▲</span> Top 5 Products
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { rank: 1, name: 'Product Alpha',   revenue: '$32,400', growth: '+14%' },
              { rank: 2, name: 'Product Beta',    revenue: '$21,000', growth: '+9%'  },
              { rank: 3, name: 'Product Gamma',   revenue: '$17,800', growth: '+7%'  },
              { rank: 4, name: 'Product Delta',   revenue: '$9,300',  growth: '+3%'  },
              { rank: 5, name: 'Product Epsilon', revenue: '$4,000',  growth: '+1%'  },
            ].map(item => (
              <div key={item.rank} style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: '#10b98120', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: '700', flexShrink: 0 }}>
                  {item.rank}
                </div>
                <span style={{ flex: 1, fontSize: '14px' }}>{item.name}</span>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>{item.revenue}</span>
                <span style={{ fontSize: '12px', color: '#10b981', background: '#10b98118', padding: '2px 8px', borderRadius: '20px' }}>{item.growth}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Worst 5 Products */}
        <div className="surface">
          <h3 className="outfit" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#ef4444' }}>▼</span> Worst 5 Products
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { rank: 1, name: 'Product Zeta',  revenue: '$1,200', growth: '-18%' },
              { rank: 2, name: 'Product Eta',   revenue: '$2,100', growth: '-12%' },
              { rank: 3, name: 'Product Theta', revenue: '$3,400', growth: '-9%'  },
              { rank: 4, name: 'Product Iota',  revenue: '$3,950', growth: '-6%'  },
              { rank: 5, name: 'Product Kappa', revenue: '$4,800', growth: '-2%'  },
            ].map(item => (
              <div key={item.rank} style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: '#ef444420', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: '700', flexShrink: 0 }}>
                  {item.rank}
                </div>
                <span style={{ flex: 1, fontSize: '14px' }}>{item.name}</span>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>{item.revenue}</span>
                <span style={{ fontSize: '12px', color: '#ef4444', background: '#ef444418', padding: '2px 8px', borderRadius: '20px' }}>{item.growth}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Top / Worst Regions & Campaigns ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
        {/* Top 5 */}
        <div className="surface">
          <h3 className="outfit" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#10b981' }}>▲</span> Top 5 Regions / Campaigns
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { rank: 1, name: 'Beirut — Summer Sale',     revenue: '$28,000', growth: '+22%' },
              { rank: 2, name: 'Dubai — Brand Awareness',  revenue: '$22,500', growth: '+17%' },
              { rank: 3, name: 'Riyadh — Flash Deals',     revenue: '$18,000', growth: '+11%' },
              { rank: 4, name: 'Cairo — Ramadan Campaign', revenue: '$10,500', growth: '+8%'  },
              { rank: 5, name: 'Amman — Loyalty Promo',    revenue: '$5,500',  growth: '+4%'  },
            ].map(item => (
              <div key={item.rank} style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: '#10b98120', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: '700', flexShrink: 0 }}>
                  {item.rank}
                </div>
                <span style={{ flex: 1, fontSize: '14px' }}>{item.name}</span>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>{item.revenue}</span>
                <span style={{ fontSize: '12px', color: '#10b981', background: '#10b98118', padding: '2px 8px', borderRadius: '20px' }}>{item.growth}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Worst 5 */}
        <div className="surface">
          <h3 className="outfit" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#ef4444' }}>▼</span> Worst 5 Regions / Campaigns
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { rank: 1, name: 'Tripoli — Retargeting',  revenue: '$820',   growth: '-24%' },
              { rank: 2, name: 'Aden — Cold Outreach',   revenue: '$1,100', growth: '-19%' },
              { rank: 3, name: 'Mosul — Display Ads',    revenue: '$1,850', growth: '-13%' },
              { rank: 4, name: 'Zarqa — Email Blast',    revenue: '$2,200', growth: '-8%'  },
              { rank: 5, name: 'Irbid — Push Campaign',  revenue: '$3,100', growth: '-4%'  },
            ].map(item => (
              <div key={item.rank} style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: '#ef444420', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: '700', flexShrink: 0 }}>
                  {item.rank}
                </div>
                <span style={{ flex: 1, fontSize: '14px' }}>{item.name}</span>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>{item.revenue}</span>
                <span style={{ fontSize: '12px', color: '#ef4444', background: '#ef444418', padding: '2px 8px', borderRadius: '20px' }}>{item.growth}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Full-Width Alerts Panel ── */}
      <div className="surface" style={{ marginTop: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 className="outfit" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px' }}>🔔</span> System Alerts
          </h3>
          <button onClick={() => setAlerts([])} className="btn btn-ghost" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Dismiss All
          </button>
        </div>

        {alerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)', fontSize: '14px' }}>
            ✅ No active alerts
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {alerts.map((alert, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: '16px',
                padding: '14px 18px', borderRadius: '10px',
                background: alert.bg, border: `1px solid ${alert.border}`,
              }}>
                <span style={{ fontSize: '16px', flexShrink: 0, marginTop: '2px' }}>{alert.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                    <span style={{ fontWeight: '600', fontSize: '14px', color: alert.color }}>{alert.title}</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)', flexShrink: 0 }}>{alert.time}</span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.5' }}>{alert.desc}</p>
                </div>
                <button
                  onClick={() => setAlerts(prev => prev.filter((_, idx) => idx !== i))}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '18px', padding: '0 4px', flexShrink: 0, lineHeight: 1 }}
                >×</button>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};

export default Dashboard;
