import React, { useState, useMemo, useEffect } from 'react';
import { 
  Search, Download, Eye, X, ChevronDown, 
  ArrowUpDown, Calendar, Columns, RefreshCw, AlertCircle
} from 'lucide-react';
import dataService from '../../services/dataService';

const COLUMNS = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Product Name' },
  { key: 'category', label: 'Category' },
  { key: 'stock', label: 'Inventory' },
  { key: 'velocity', label: 'Velocity' },
  { key: 'risk', label: 'Risk Level' }
];

// ─── Explorer Component ─────────────────────────────────────────────────────
const Explorer = ({ setTab, setGlobalProductId }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'id', direction: 'asc' });
  const [visibleColumns, setVisibleColumns] = useState(COLUMNS.map(c => c.key));
  const [selectedRow, setSelectedRow] = useState(null);
  const [showColMenu, setShowColMenu] = useState(false);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const res = await dataService.getInventory(search);
      setData(res || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  // Sorting Logic
  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Filtering Logic (Client side for now as primary search)
  const filteredData = useMemo(() => {
    return data.filter(item => 
      Object.values(item).some(val => 
        String(val).toLowerCase().includes(search.toLowerCase())
      )
    ).sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
      if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, search, sortConfig]);

  const toggleColumn = (key) => {
    setVisibleColumns(prev => 
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    );
  };

  const handleExportCSV = () => {
    const headers = visibleColumns.join(',');
    const rows = filteredData.map(row => 
      visibleColumns.map(col => row[col]).join(',')
    ).join('\n');
    const csvContent = "data:text/csv;charset=utf-8," + headers + "\n" + rows;
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "orion_ledger_export.csv");
    document.body.appendChild(link);
    link.click();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* ── Header & Toolbar ── */}
      <div className="surface glass" style={{ padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="outfit" style={{ fontSize: '26px', marginBottom: '4px' }}>Data Explorer</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Audit, filter, and export raw inventory datasets.</p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
           <button onClick={handleExportCSV} className="btn btn-ghost" style={{ border: '1px solid var(--border-color)', display: 'flex', gap: '8px' }} disabled={data.length === 0}>
              <Download size={18} /> Export CSV
           </button>
           <button onClick={fetchInventory} className="btn btn-primary" style={{ display: 'flex', gap: '8px' }} disabled={loading}>
              <RefreshCw size={18} className={loading ? 'spin' : ''} /> Refresh Data
           </button>
        </div>
      </div>

      {/* ── Controls ── */}
      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <input 
            type="text" 
            placeholder="Search SKUs, names, categories..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%', padding: '12px 16px 12px 48px', borderRadius: '12px',
              border: '1px solid var(--border-color)', background: 'var(--surface-color)',
              color: 'var(--text-primary)', outline: 'none'
            }}
          />
          <Search size={18} color="var(--text-secondary)" style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)' }} />
        </div>

        <div style={{ position: 'relative' }}>
          <button 
             onClick={() => setShowColMenu(!showColMenu)}
             className="btn btn-ghost" 
             style={{ border: '1px solid var(--border-color)', borderRadius: '12px', display: 'flex', gap: '8px' }}
          >
            <Columns size={18} /> Columns <ChevronDown size={14} />
          </button>
          
          {showColMenu && (
            <div className="surface glass" style={{ position: 'absolute', top: '100%', right: 0, marginTop: '8px', zIndex: 50, padding: '12px', minWidth: '180px', borderRadius: '14px', border: '1px solid var(--border-color)', boxShadow: '0 10px 30px rgba(0,0,0,0.3)' }}>
              {COLUMNS.map(col => (
                <label key={col.key} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px', cursor: 'pointer', fontSize: '13px' }}>
                  <input type="checkbox" checked={visibleColumns.includes(col.key)} onChange={() => toggleColumn(col.key)} />
                  {col.label}
                </label>
              ))}
            </div>
          )}
        </div>

        <button className="btn btn-ghost" style={{ border: '1px solid var(--border-color)', borderRadius: '12px', display: 'flex', gap: '8px' }}>
           <Calendar size={18} /> Filters
        </button>
      </div>

      {/* ── Table Area ── */}
      <div className="surface" style={{ padding: '0', overflow: 'hidden', minHeight: '300px', position: 'relative' }}>
        {loading && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.01)', backdropFilter: 'blur(6px)', zIndex: 10 }}>
            <div style={{ textAlign: 'center' }}>
              <RefreshCw size={32} color="var(--accent-color)" className="spin" style={{ marginBottom: '12px' }} />
              <p className="outfit" style={{ fontSize: '14px', fontWeight: '600' }}>Synchronizing Inventory Records...</p>
            </div>
          </div>
        )}

        {!loading && filteredData.length === 0 && (
          <div style={{ padding: '80px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
             <AlertCircle size={40} style={{ margin: '0 auto 16px', opacity: 0.2 }} />
             <p>No inventory records matched your query.</p>
          </div>
        )}

        {filteredData.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'var(--surface-hover)', borderBottom: '1px solid var(--border-color)' }}>
                  {COLUMNS.filter(c => visibleColumns.includes(c.key)).map(col => (
                    <th 
                      key={col.key} 
                      onClick={() => handleSort(col.key)}
                      style={{ padding: '16px 20px', fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', cursor: 'pointer' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {col.label} <ArrowUpDown size={12} />
                      </div>
                    </th>
                  ))}
                  <th style={{ padding: '16px 20px' }}></th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((row) => (
                  <tr key={row.id} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.2s' }} onMouseOver={e => e.currentTarget.style.background = 'var(--surface-hover)'} onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                    {COLUMNS.filter(c => visibleColumns.includes(c.key)).map(col => (
                      <td key={col.key} style={{ padding: '16px 20px', fontSize: '13px' }}>
                        {col.key === 'risk' ? (
                          <span style={{ padding: '4px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: '600', background: row[col.key] === 'Low' ? '#10b98115' : '#ef444415', color: row[col.key] === 'Low' ? '#10b981' : '#ef4444' }}>
                            {row[col.key]}
                          </span>
                        ) : row[col.key]}
                      </td>
                    ))}
                    <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                      <button onClick={() => setSelectedRow(row)} className="btn btn-ghost" style={{ padding: '6px' }}><Eye size={16} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-color)', color: 'var(--text-secondary)', fontSize: '12px' }}>
           Showing {filteredData.length} active records
        </div>
      </div>

      {/* ── Row Details Modal ── */}
      {selectedRow && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
           <div className="surface" style={{ width: '500px', padding: '32px', position: 'relative' }}>
              <button onClick={() => setSelectedRow(null)} style={{ position: 'absolute', top: '24px', right: '24px', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                 <X size={24} />
              </button>
              
              <h2 className="outfit" style={{ fontSize: '22px', marginBottom: '8px' }}>SKU Audit Detail</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '24px' }}>Metadata consistency check for product ID: {selectedRow.id}</p>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                 {Object.entries(selectedRow).map(([key, val]) => (
                   <div key={key}>
                      <label style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: 'bold' }}>{key}</label>
                      <div style={{ fontSize: '14px' }}>{val}</div>
                   </div>
                 ))}
              </div>

              <div style={{ marginTop: '32px', display: 'flex', gap: '12px' }}>
                 <button onClick={() => setSelectedRow(null)} className="btn btn-primary" style={{ flex: 1 }}>Dismiss</button>
                 <button 
                  onClick={() => {
                    setGlobalProductId(selectedRow.id.toString());
                    setTab('vision');
                    setSelectedRow(null);
                  }}
                  className="btn btn-ghost" 
                  style={{ border: '1px solid var(--border-color)', flex: 1 }}
                >
                  Generate Forecast
                </button>
              </div>
           </div>
        </div>
      )}

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default Explorer;
