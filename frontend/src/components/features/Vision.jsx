import React, { useState, useEffect, useRef } from 'react';
import {
  Zap, Calendar, Crosshair, AlertCircle, RefreshCw,
  TrendingUp, Activity, BarChart3, Settings2, Box, Search, ChevronDown, User
} from 'lucide-react';
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine
} from 'recharts';
import { aiService } from '../../services/api';

// ─── Mock Product Data for Search ───────────────────────────────────────────
const MOCK_PRODUCTS = [
  { id: '1', name: 'Product Alpha' },
  { id: '102', name: 'Premium Ceramic Bowl' },
  { id: '505', name: 'Vintage Tea Set' },
  { id: '1004', name: 'Handcrafted Vase' },
  { id: '2020', name: 'Minimalist Plate' },
  { id: '3045', name: 'Stoneware Mug' },
];

// ─── Shared UI Components ──────────────────────────────────────────────────
const InputGroup = ({ label, icon: Icon, children, style = {} }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, ...style }}>
    <label style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
      {label}
    </label>
    <div style={{ position: 'relative' }}>
      {children}
      {Icon && <Icon size={16} color="var(--text-secondary)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />}
    </div>
  </div>
);

const inputBaseStyle = {
  width: '100%',
  padding: '12px 12px 12px 38px',
  borderRadius: '12px',
  border: '1px solid var(--border-color)',
  background: 'var(--bg-color)',
  color: 'var(--text-primary)',
  fontFamily: 'inherit',
  fontSize: '14px',
  outline: 'none',
  transition: 'all 0.2s ease',
};

// ─── Product Search Dropdown Component ─────────────────────────────────────
const ProductSelector = ({ selectedId, onSelect }) => {
  const [searchMode, setSearchMode] = useState('name'); // 'id' or 'name'
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const filtered = MOCK_PRODUCTS.filter(p =>
    p.name.toLowerCase().includes(query.toLowerCase()) || p.id.includes(query)
  );

  const selectedProduct = MOCK_PRODUCTS.find(p => p.id === selectedId);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={dropdownRef} style={{ position: 'relative', width: '380px', display: 'flex', gap: '12px' }}>

      {/* Search Mode Toggle */}
      <div style={{ display: 'flex', background: 'var(--surface-hover)', borderRadius: '10px', padding: '2px', alignSelf: 'flex-end' }}>
        <button
          onClick={() => setSearchMode('id')}
          style={{ padding: '4px 10px', fontSize: '11px', border: 'none', borderRadius: '7px', cursor: 'pointer', background: searchMode === 'id' ? 'var(--accent-color)' : 'transparent', color: searchMode === 'id' ? '#000' : 'var(--text-secondary)' }}
        >ID</button>
        <button
          onClick={() => setSearchMode('name')}
          style={{ padding: '4px 10px', fontSize: '11px', border: 'none', borderRadius: '7px', cursor: 'pointer', background: searchMode === 'name' ? 'var(--accent-color)' : 'transparent', color: searchMode === 'name' ? '#000' : 'var(--text-secondary)' }}
        >Name</button>
      </div>

      <div style={{ flex: 1, position: 'relative' }}>
        <InputGroup label={searchMode === 'id' ? "Product ID" : "Product Name"} icon={searchMode === 'id' ? Box : Search}>
          <input
            style={inputBaseStyle}
            placeholder={searchMode === 'id' ? "Enter numerical ID..." : "Start typing product name..."}
            value={isOpen ? query : (selectedProduct ? (searchMode === 'id' ? selectedProduct.id : selectedProduct.name) : query)}
            onFocus={() => setIsOpen(true)}
            onChange={(e) => { setQuery(e.target.value); setIsOpen(true); }}
          />
        </InputGroup>

        {isOpen && (
          <div className="surface glass" style={{
            position: 'absolute', top: '100%', left: 0, right: 0, marginTop: '8px', zIndex: 100,
            maxHeight: '220px', overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: '14px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.3)', padding: '6px'
          }}>
            {filtered.length > 0 ? filtered.map(p => (
              <div
                key={p.id}
                onClick={() => { onSelect(p.id); setIsOpen(false); setQuery(''); }}
                style={{
                  padding: '10px 14px', borderRadius: '8px', cursor: 'pointer', fontSize: '13px',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'var(--surface-hover)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <span style={{ fontWeight: '500' }}>{p.name}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', background: 'var(--border-color)', padding: '2px 6px', borderRadius: '4px' }}>#{p.id}</span>
              </div>
            )) : (
              <div style={{ padding: '20px', textAlign: 'center', fontSize: '12px', color: 'var(--text-secondary)' }}>
                No matching products found
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Main Vision Component ──────────────────────────────────────────────────
const Vision = () => {
  const [globalProductId, setGlobalProductId] = useState('1');

  // ── Predict State ──
  const [pLoading, setPLoading] = useState(false);
  const [pData, setPData] = useState(null);
  const [pError, setPError] = useState(null);
  const [pDates, setPDates] = useState({ start: '2023-01-01', end: '2023-01-31' });

  // ── Forecast State ──
  const [fLoading, setFLoading] = useState(false);
  const [fData, setFData] = useState(null);
  const [fError, setFError] = useState(null);
  const [fHorizon, setFHorizon] = useState('28');

  const handlePredict = async () => {
    if (!globalProductId) return;
    setPLoading(true);
    setPError(null);
    try {
      const res = await aiService.predictDemand({
        product_id: parseInt(globalProductId),
        features: ['quantity'],
        start_date: pDates.start,
        end_date: pDates.end,
      });
      setPData(res.predictions.map((val, i) => ({ name: `D${i + 1}`, val })));
    } catch (err) {
      setPError('Inference engine connection failed');
    } finally {
      setPLoading(false);
    }
  };

  const handleForecast = async () => {
    if (!globalProductId) return;
    setFLoading(true);
    setFError(null);
    try {
      const res = await aiService.getForecast(globalProductId, parseInt(fHorizon));
      setFData(Array.isArray(res) ? res : res.forecast || []);
    } catch (err) {
      setFError('ARIMA model execution failed');
    } finally {
      setFLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* ── Global Controls ── */}
      <div className="surface glass" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px 32px' }}>
        <div style={{ flex: 1 }}>
          <h1 className="outfit" style={{ fontSize: '28px', marginBottom: '4px' }}>Product Vision</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Forward-looking analytical workbench for SKU trajectories.</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <ProductSelector selectedId={globalProductId} onSelect={setGlobalProductId} />

          <div style={{ display: 'flex', gap: '12px', marginTop: '18px' }}>
            <button className="btn btn-ghost" style={{ border: '1px solid var(--border-color)', height: '44px' }}>
              <Settings2 size={18} />
            </button>
            <button onClick={() => { handlePredict(); handleForecast(); }} className="btn btn-primary" style={{ height: '44px', padding: '0 24px' }}>
              <RefreshCw size={18} /> Run All
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: '24px' }}>

        {/* ── 1. Predict Timeline ── */}
        <div className="surface" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ background: 'var(--accent-color)20', padding: '10px', borderRadius: '12px' }}>
                <Zap size={22} color="var(--accent-color)" />
              </div>
              <div>
                <h2 className="outfit" style={{ fontSize: '20px' }}>XGBoost Prediction</h2>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Baseline demand estimation via historical features.</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <InputGroup label="Time Interval" icon={Calendar}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input type="date" style={{ ...inputBaseStyle, paddingLeft: '12px', width: '135px', height: '40px' }} value={pDates.start} onChange={e => setPDates({ ...pDates, start: e.target.value })} />
                  <input type="date" style={{ ...inputBaseStyle, paddingLeft: '12px', width: '135px', height: '40px' }} value={pDates.end} onChange={e => setPDates({ ...pDates, end: e.target.value })} />
                </div>
              </InputGroup>
              <button onClick={handlePredict} className="btn btn-primary" style={{ padding: '0 20px', height: '40px', marginTop: '18px', fontSize: '13px' }} disabled={pLoading}>
                {pLoading ? <RefreshCw size={16} className="spin" /> : 'Run Predict'}
              </button>
            </div>
          </div>

          <ChartContainer loading={pLoading} data={pData} error={pError} type="predict">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={pData}>
                <defs>
                  <linearGradient id="pGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent-color)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--accent-color)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                <Tooltip contentStyle={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px' }} />
                <Area type="monotone" dataKey="val" name="Predicted Demand" stroke="var(--accent-color)" strokeWidth={3} fill="url(#pGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>

        {/* ── 2. Forecast Timeline ── */}
        <div className="surface" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ background: '#a855f720', padding: '10px', borderRadius: '12px' }}>
                <TrendingUp size={22} color="#a855f7" />
              </div>
              <div>
                <h2 className="outfit" style={{ fontSize: '20px' }}>ARIMA Forecast</h2>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Trajectory projection with confidence intervals.</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <InputGroup label="Horizon (Days)" icon={Activity}>
                <input type="number" style={{ ...inputBaseStyle, height: '40px', width: '130px' }} value={fHorizon} onChange={e => setFHorizon(e.target.value)} />
              </InputGroup>
              <button onClick={handleForecast} className="btn btn-primary" style={{ padding: '0 20px', height: '40px', marginTop: '18px', background: '#a855f7', color: '#fff', fontSize: '13px' }} disabled={fLoading}>
                {fLoading ? <RefreshCw size={16} className="spin" /> : 'Run Forecast'}
              </button>
            </div>
          </div>

          <ChartContainer loading={fLoading} data={fData} error={fError} type="forecast">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={fData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                <Tooltip contentStyle={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '12px' }} />
                <Legend verticalAlign="top" align="right" height={36} iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
                <Line type="monotone" dataKey="actual" name="Historical Actual" stroke="#a855f7" strokeWidth={3} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="forecast" name="Projected Forecast" stroke="var(--accent-color)" strokeWidth={3} strokeDasharray="5 5" dot={false} />
                <ReferenceLine y={0} stroke="var(--border-color)" />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>

      </div>

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

// ─── Helper UI States ─────────────────────────────────────────────────────────

const ChartContainer = ({ loading, data, error, type, children }) => {
  return (
    <div style={{ height: '340px', width: '100%', background: 'var(--bg-color)', borderRadius: '16px', border: '1px solid var(--border-color)', padding: '24px', position: 'relative' }}>
      {loading && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10, background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(6px)', borderRadius: '16px' }}>
          <div style={{ textAlign: 'center' }}>
            <RefreshCw size={32} color={type === 'predict' ? 'var(--accent-color)' : '#a855f7'} className="spin" style={{ margin: '0 auto 12px' }} />
            <p className="outfit" style={{ fontWeight: '600', fontSize: '14px' }}>{type === 'predict' ? 'Executing Inference...' : 'Fitting Statistical Model...'}</p>
          </div>
        </div>
      )}

      {error && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444', gap: '10px' }}>
          <AlertCircle size={20} /> <span style={{ fontWeight: '600', fontSize: '14px' }}>{error}</span>
        </div>
      )}

      {!data && !loading && !error && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', gap: '12px' }}>
          {type === 'predict' ? <Zap size={40} style={{ opacity: 0.1 }} /> : <TrendingUp size={40} style={{ opacity: 0.1 }} />}
          <p style={{ fontSize: '14px', fontWeight: '500' }}>Select a product and configure parameters to see the vision.</p>
        </div>
      )}

      {data && children}
    </div>
  );
};

export default Vision;
