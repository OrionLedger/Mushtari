import React, { useEffect, useState } from 'react';
import { Wifi, WifiOff, DollarSign, Percent, PieChart, RefreshCw, AlertCircle } from 'lucide-react';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar,
} from 'recharts';
import dataService from '../../services/dataService';

// ─── Scope Toggle Configuration ───────────────────────────────────────────────
const SCOPES = [
  { id: 'day',       label: 'Day'       },
  { id: 'week',      label: 'Week'      },
  { id: 'month',     label: 'Month'     },
  { id: 'year',      label: 'Year'      },
  { id: '5years',    label: '5 Years'   },
  { id: 'beginning', label: 'Beginning' },
];

const BAR_COLOR = '#2dd4bf';

// ─── Sub-components ─────────────────────────────────────────────────────────────

const LoadingOverlay = ({ message = "Synchronizing Data..." }) => (
  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10, background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(4px)', borderRadius: '16px' }}>
    <div style={{ textAlign: 'center' }}>
      <RefreshCw size={24} color="var(--accent-color)" className="spin" style={{ margin: '0 auto 12px' }} />
      <p style={{ fontSize: '12px', fontWeight: '500' }}>{message}</p>
    </div>
  </div>
);

const DemandChart = () => {
  const [chartScope, setChartScope] = useState('week');
  const [data, setData]             = useState([]);
  const [loading, setLoading]       = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await dataService.getAggregatedDemand(chartScope);
        setData(res || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [chartScope]);

  return (
    <div className="surface" style={{ marginTop: '32px', height: '400px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h3 className="outfit">Global Demand</h3>
        <div style={{ display: 'flex', gap: '4px', background: 'var(--surface-hover)', padding: '4px', borderRadius: '10px' }}>
          {SCOPES.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setChartScope(id)}
              style={{
                padding: '6px 14px', fontSize: '11px', fontFamily: 'inherit',
                fontWeight: chartScope === id ? '600' : '400',
                borderRadius: '7px', border: 'none', cursor: 'pointer',
                transition: 'all 0.18s ease',
                background: chartScope === id ? 'var(--accent-color)' : 'transparent',
                color:      chartScope === id ? '#0f172a' : 'var(--text-secondary)',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      
      {loading && <LoadingOverlay message="Fetching global trends..." />}
      
      {!loading && data.length === 0 && (
         <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
            <AlertCircle size={20} style={{ marginRight: '8px' }} /> No demand data for this scope yet.
         </div>
      )}

      {data.length > 0 && (
        <div style={{ flex: 1 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="var(--accent-color)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--accent-color)" stopOpacity={0}   />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px', color: 'var(--text-primary)', fontSize: '12px' }} />
              <Area type="monotone" dataKey="sales"    name="Historical Sales" stroke="var(--accent-color)"    strokeWidth={3} fillOpacity={1} fill="url(#colorSales)" />
              <Area type="monotone" dataKey="forecast" name="Projected"        stroke="var(--text-secondary)" strokeDasharray="5 5" strokeWidth={2} fillOpacity={0} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

// ─── Main Dashboard ──────────────────────────────────────────────────────────────
const Dashboard = () => {
  const [apiStatus, setApiStatus]     = useState(null);
  const [kpis, setKpis]               = useState(null);
  const [revenueData, setRevenueData] = useState([]);
  const [revLoading, setRevLoading]   = useState(false);

  const [alerts, setAlerts]           = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const health = await dataService.getHealth();
        setApiStatus('ok');
        const kpiRes = await dataService.getKPIs();
        setKpis(kpiRes);
      } catch (err) {
        setApiStatus('error');
      }
    };
    init();
  }, []);

  useEffect(() => {
    const loadRevenue = async () => {
      setRevLoading(true);
      try {
        const data = await dataService.getBreakdown('product');
        setRevenueData(data || []);
      } catch (err) { console.error(err); }
      finally { setRevLoading(false); }
    };
    loadRevenue();
  }, []);

  useEffect(() => {
    const loadAlerts = async () => {
      setAlertsLoading(true);
      try {
        const data = await dataService.getSystemAlerts();
        setAlerts(data || []);
      } catch (err) { console.error(err); }
      finally { setAlertsLoading(false); }
    };
    loadAlerts();
  }, []);



  return (
    <div className="dashboard">

      {/* ── API Status ── */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
        {apiStatus === null && (
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', padding: '6px 14px', borderRadius: '20px', background: 'var(--surface-hover)' }}>
            Checking status...
          </span>
        )}
        {apiStatus === 'ok' && (
          <span style={{ fontSize: '12px', color: '#10b981', padding: '6px 14px', borderRadius: '20px', background: '#10b98120', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Wifi size={14} /> Systems Online
          </span>
        )}
        {apiStatus === 'error' && (
          <span style={{ fontSize: '12px', color: '#f59e0b', padding: '6px 14px', borderRadius: '20px', background: '#f59e0b20', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <WifiOff size={14} /> Backend Latency — Verification Required
          </span>
        )}
      </div>

      {/* ── KPI Cards ── */}
      <div className="card-grid">
         {[
           { label: 'Net Revenue', value: kpis?.revenue || '---', icon: <DollarSign size={20} />, color: '#10b981', change: kpis?.revenue_change },
           { label: 'Growth Output', value: kpis?.growth || '---', icon: <Percent size={20} />, color: '#3b82f6', change: kpis?.growth_change },
           { label: 'Profit Yield', value: kpis?.margin || '---', icon: <PieChart size={20} />, color: '#a855f7' },
         ].map((stat, i) => (
          <div key={i} className="surface" style={{ position: 'relative' }}>
            {!kpis && <div style={{ position: 'absolute', inset: 0, background: 'var(--surface-color)', opacity: 0.5, borderRadius: '16px' }} />}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '500' }}>{stat.label}</span>
              <div style={{ color: stat.color }}>{stat.icon}</div>
            </div>
            <div className="outfit" style={{ fontSize: '30px', fontWeight: '700', marginTop: '12px' }}>{stat.value}</div>
            {stat.change && (
              <div style={{ color: '#10b981', fontSize: '11px', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span>↑ {stat.change}</span>
                <span style={{ color: 'var(--text-secondary)' }}>vs prev.</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ── Demand Chart ── */}
      <DemandChart />

      {/* ── Revenue Breakdown ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px', marginTop: '24px' }}>
        <div className="surface" style={{ display: 'flex', flexDirection: 'column', position: 'relative' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 className="outfit">Revenue Breakdown</h3>
          </div>
          {revLoading && <LoadingOverlay />}
          {!revLoading && revenueData.length === 0 && <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>No revenue data yet.</div>}
          {revenueData.length > 0 && (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={revenueData} layout="vertical" margin={{ left: 0, right: 20 }}>
                <XAxis type="number" stroke="var(--text-secondary)" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={85} />
                <Tooltip formatter={v => [`$${v.toLocaleString()}`, 'Value']} contentStyle={{ backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="value" fill={BAR_COLOR} radius={[0, 6, 6, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── System Alerts Panel ── */}
      <div className="surface" style={{ marginTop: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 className="outfit" style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '16px' }}>
            🔔 Insight Stream
          </h3>
          <button onClick={async () => { try { await dataService.markAllAlertsRead(); setAlerts([]); } catch (e) { console.error(e); } }} className="btn btn-ghost" style={{ fontSize: '11px', color: 'var(--text-secondary)' }} disabled={alerts.length === 0}>
            Mark All Read
          </button>
        </div>

        {alertsLoading && (
          <div style={{ padding: '32px', textAlign: 'center' }}>
             <RefreshCw size={20} className="spin" color="var(--accent-color)" />
          </div>
        )}

        {!alertsLoading && alerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)', fontSize: '13px' }}>
            All systems nominal. No active alerts.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {alerts.map((alert, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: '16px',
                padding: '12px 16px', borderRadius: '12px',
                background: alert.bg, border: `1px solid ${alert.border}`,
              }}>
                <span style={{ fontSize: '14px', flexShrink: 0, marginTop: '2px' }}>{alert.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                    <span style={{ fontWeight: '600', fontSize: '13px', color: alert.color }}>{alert.title}</span>
                    <span style={{ fontSize: '10px', color: 'var(--text-secondary)', flexShrink: 0 }}>{alert.time}</span>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px', lineHeight: '1.5' }}>{alert.desc}</p>
                </div>
                <button
                  onClick={async () => {
                    try {
                      setAlerts(prev => prev.filter((_, idx) => idx !== i));
                      await dataService.resolveAlert(alert.id, alert.severity, alert.ts);
                    } catch (err) {
                      console.error("Delayed resolve fail:", err);
                    }
                  }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '16px', padding: '0 4px', flexShrink: 0 }}
                >×</button>
              </div>
            ))}
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

export default Dashboard;
