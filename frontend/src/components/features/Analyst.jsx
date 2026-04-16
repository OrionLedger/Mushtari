import React, { useState, useMemo } from 'react';
import {
  Search, Sparkles, AlertCircle, RefreshCw,
  TrendingUp, Layers, PieChart as PieIcon,
  BarChart3, LineChart as LineIcon, Info,
  CheckCircle2, AlertTriangle, Lightbulb
} from 'lucide-react';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, Cell, PieChart as RePie, Pie, LineChart as ReLine, Line,
  Legend
} from 'recharts';
import { irsService } from '../../services/irsService';
import { Download } from 'lucide-react';

// ─── IRS Schema Definition & Mock Logic ────────────────────────────────────

/* 
  SCHEMA:
  {
    title: string,
    insight: string,
    visuals: [
      { 
        chart_type: 'line' | 'bar' | 'pie' | 'funnel', 
        title: string,
        metric: string, 
        dimension: string,
        data: Array<any>
      }
    ],
    alerts: [ { type: 'info' | 'warning', message: string } ],
    layout: 'stack' | 'grid'
  }
*/

const MOCK_IRS_RESPONSE = null; // Legacy mock removed in favor of external loading

// ─── Sub-Components ────────────────────────────────────────────────────────

const AlertsPanel = ({ alerts }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
    {alerts.map((alert, i) => (
      <div key={i} style={{
        padding: '14px 20px', borderRadius: '12px', border: '1px solid',
        display: 'flex', alignItems: 'center', gap: '12px', fontSize: '14px',
        background: alert.type === 'warning' ? '#f59e0b10' : '#3b82f610',
        borderColor: alert.type === 'warning' ? '#f59e0b30' : '#3b82f630',
        color: alert.type === 'warning' ? '#f59e0b' : '#3b82f6'
      }}>
        {alert.type === 'warning' ? <AlertTriangle size={18} /> : <Info size={18} />}
        <span style={{ fontWeight: '500' }}>{alert.message}</span>
      </div>
    ))}
  </div>
);

const InsightBlock = ({ title, text }) => (
  <div className="surface" style={{ padding: '32px', marginBottom: '24px', position: 'relative', overflow: 'hidden' }}>
    <div style={{ position: 'absolute', top: '-10px', right: '-10px', opacity: 0.1 }}>
       <Lightbulb size={120} color="var(--accent-color)" />
    </div>
    <h2 className="outfit" style={{ fontSize: '26px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
      <Sparkles size={24} color="var(--accent-color)" /> {title}
    </h2>
    <div style={{ padding: '20px', background: 'var(--surface-hover)', borderRadius: '16px', borderLeft: '4px solid var(--accent-color)' }}>
       <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: '1.7', margin: 0 }}>
          {text}
       </p>
    </div>
  </div>
);

const ChartRenderer = ({ visual }) => {
  const { chart_type, data, title } = visual;
  
  return (
    <div className="surface" style={{ padding: '24px', flex: 1, minHeight: '340px' }}>
      <h3 className="outfit" style={{ fontSize: '16px', marginBottom: '20px', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
        {title}
        {chart_type === 'line' && <LineIcon size={16} />}
        {chart_type === 'bar' && <BarChart3 size={16} />}
        {chart_type === 'pie' && <PieIcon size={16} />}
      </h3>
      
      <div style={{ height: '260px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          {chart_type === 'line' ? (
            <ReLine data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 12, fill: 'var(--text-secondary)'}} />
              <YAxis axisLine={false} tickLine={false} tick={{fontSize: 12, fill: 'var(--text-secondary)'}} />
              <Tooltip contentStyle={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px' }} />
              <Line type="monotone" dataKey="val" stroke="var(--accent-color)" strokeWidth={3} dot={{r: 4, fill: 'var(--accent-color)'}} activeDot={{r: 6}} />
            </ReLine>
          ) : chart_type === 'bar' ? (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 12, fill: 'var(--text-secondary)'}} />
              <YAxis axisLine={false} tickLine={false} tick={{fontSize: 12, fill: 'var(--text-secondary)'}} />
              <Tooltip cursor={{fill: 'var(--surface-hover)'}} contentStyle={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px' }} />
              <Bar dataKey="val" radius={[4, 4, 0, 0]} barSize={32}>
                {data.map((entry, i) => <Cell key={i} fill={i % 2 === 0 ? 'var(--accent-color)' : '#a855f7'} />)}
              </Bar>
            </BarChart>
          ) : chart_type === 'pie' ? (
            <RePie>
              <Pie data={data} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="val">
                {data.map((entry, index) => <Cell key={index} fill={entry.fill} />)}
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px' }} />
              <Legend verticalAlign="bottom" align="center" iconType="circle" />
            </RePie>
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                Unsupported Chart Type: {chart_type}
            </div>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// ─── Main IRS Renderer ──────────────────────────────────────────────────────

const IRSRenderer = ({ schema }) => {
  if (!schema) return (
    <div style={{ padding: '60px', textAlign: 'center', opacity: 0.5 }}>
      <RefreshCw size={40} className="spin" style={{ marginBottom: '16px' }} />
      <p className="outfit">Parsing Insight Schema...</p>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <AlertsPanel alerts={schema.alerts || []} />
      <InsightBlock title={schema.title} text={schema.insight} />
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: schema.layout === 'grid' ? 'repeat(auto-fit, minmax(400px, 1fr))' : '1fr', 
        gap: '24px' 
      }}>
        {schema.visuals.map((vis, i) => (
          <ChartRenderer key={i} visual={vis} />
        ))}
      </div>
    </div>
  );
};

// ─── Component Entry Point ──────────────────────────────────────────────────

const Analyst = () => {
  const [query, setQuery] = useState('');
  const [irsData, setIrsData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const processQuery = async () => {
    setIsProcessing(true);
    setIrsData(null);
    try {
      // Direct load from external schema file
      const data = await irsService.loadSchema('insight_schema.json');
      setIrsData(data);
    } catch (err) {
      console.error("Inference Error:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* ── Search Command Bar ── */}
      <div className="surface glass" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
           <Sparkles size={24} color="var(--accent-color)" />
           <h2 className="outfit" style={{ fontSize: '22px' }}>Insight Engine</h2>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'var(--bg-color)', padding: '8px', borderRadius: '20px', border: '1px solid var(--border-color)', boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}>
          <div style={{ position: 'relative', flex: 1, display: 'flex', alignItems: 'center' }}>
            <Search size={20} color="var(--text-secondary)" style={{ position: 'absolute', left: '16px' }} />
            <input 
              type="text" 
              placeholder="Search patterns, predict outcomes, or audit segments..." 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                width: '100%', padding: '12px 16px 12px 48px', borderRadius: '14px',
                border: 'none', background: 'transparent',
                color: 'var(--text-primary)', fontSize: '15px', outline: 'none'
              }}
            />
          </div>
          
          <button 
            onClick={processQuery}
            disabled={isProcessing}
            style={{
              padding: '10px 24px', borderRadius: '12px', fontWeight: 'bold', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '8px', transition: 'all 0.2s',
              background: 'var(--accent-color)', color: '#0f172a', border: 'none',
              boxShadow: '0 4px 12px rgba(45, 212, 191, 0.2)',
              whiteSpace: 'nowrap', flexShrink: 0
            }}
          >
            {isProcessing ? <RefreshCw size={18} className="spin" /> : <><TrendingUp size={18} /> Generate Insights</>}
          </button>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          {['Check ROI', 'Sales Velocity', 'Segment Growth'].map(tag => (
            <button key={tag} onClick={() => setQuery(tag)} style={{ background: 'var(--surface-hover)', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', padding: '6px 14px', borderRadius: '80px', fontSize: '12px', cursor: 'pointer' }}>
               {tag}
            </button>
          ))}
        </div>
      </div>

      {/* ── IRS Renderer Target ── */}
      <IRSRenderer schema={irsData} />

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default Analyst;
