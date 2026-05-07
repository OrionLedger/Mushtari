import React, { useState, useEffect } from 'react';
import { 
  FileText, Download, Filter, Search, 
  ExternalLink, Trash2, Calendar, FileType,
  RefreshCw, Archive
} from 'lucide-react';
import dataService from '../../services/dataService';

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState('');
  
  // ── Generation State ──
  const [showGenModal, setShowGenModal] = useState(false);
  const [genForm, setGenForm]           = useState({ name: '', type: 'PDF' });
  const [generating, setGenerating]     = useState(false);
  
  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await dataService.getReports();
      // Map DB fields to UI-friendly fields
      const mapped = (data || []).map(r => ({
        id: r.id,
        name: r.name,
        type: r.report_type || 'PDF',
        size: r.file_size_kb ? `${(r.file_size_kb / 1024).toFixed(1)} MB` : '0.1 MB',
        date: r.created_at ? new Date(r.created_at).toISOString().slice(0, 10) : '2024-04-17'
      })).sort((a,b) => b.id - a.id);
      
      setReports(mapped);
    } catch (err) {
      console.error("Failed to load reports:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setGenerating(true);
    try {
      // Pass custom name if provided, else use default
      const payload = {
         name: genForm.name.trim() || `Demand_Audit_${new Date().toISOString().slice(0,10)}`,
         type: genForm.type
      };
      await dataService.generateReport(payload);
      setShowGenModal(false);
      setGenForm({ name: '', type: 'PDF' });
      await loadReports();
    } catch (err) {
      alert("Generation failed: " + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const filteredReports = reports.filter(r => 
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* ── Header ── */}
      <div className="surface glass" style={{ padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="outfit" style={{ fontSize: '28px', marginBottom: '4px' }}>Reports & Audits</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Access and download generated analytical documentation.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <div style={{ position: 'relative' }}>
             <Search size={18} color="var(--text-secondary)" style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)' }} />
             <input 
                type="text" 
                placeholder="Search report name..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ background: 'var(--bg-color)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '10px 16px 10px 48px', color: 'var(--text-primary)', fontSize: '14px', outline: 'none' }}
             />
          </div>
          <button onClick={() => setShowGenModal(true)} className="btn btn-primary" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
             <FileType size={18} /> Generate New
          </button>
        </div>
      </div>

      {loading && (
        <div style={{ padding: '80px', textAlign: 'center' }}>
           <RefreshCw size={40} className="spin" style={{ margin: '0 auto 16px', color: 'var(--accent-color)' }} />
           <p className="outfit">Scanning generated documents...</p>
        </div>
      )}

      {!loading && filteredReports.length === 0 && (
        <div style={{ padding: '80px', textAlign: 'center', opacity: 0.5 }}>
           <Archive size={48} style={{ margin: '0 auto 16px' }} />
           <p>No reports found matching your criteria.</p>
        </div>
      )}

      {/* ── Reports Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
        {filteredReports.map(report => (
          <div key={report.id} className="surface" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', transition: 'transform 0.2s' }} onMouseOver={e => e.currentTarget.style.transform = 'translateY(-4px)'} onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
               <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'var(--bg-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border-color)' }}>
                  <FileText size={24} color={report.type === 'PDF' ? '#ef4444' : '#10b981'} />
               </div>
               <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 'bold', background: 'var(--surface-hover)', padding: '4px 8px', borderRadius: '6px' }}>
                  {report.size}
               </span>
            </div>

            <div>
               <h3 className="outfit" style={{ fontSize: '18px', marginBottom: '8px' }}>{report.name}</h3>
               <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Calendar size={14} /> Created {report.date}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileType size={14} /> Format: {report.type}
                  </div>
               </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
               <button 
                onClick={() => alert(`Starting download for: ${report.name}`)}
                className="btn btn-ghost" 
                style={{ flex: 1, border: '1px solid var(--border-color)', display: 'flex', gap: '8px', justifyContent: 'center' }}
              >
                  <Download size={16} /> Download
               </button>
               <button 
                  onClick={async () => {
                    if (window.confirm(`Are you sure you want to delete ${report.name}?`)) {
                      await dataService.deleteReport(report.id);
                      await loadReports();
                    }
                  }}
                  className="btn btn-ghost" 
                  style={{ padding: '8px', color: '#ef4444' }}
                >
                  <Trash2 size={18} />
               </button>
            </div>
          </div>
        ))}
      </div>

      {/* ── Generation Modal ── */}
      {showGenModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
           <form onSubmit={handleGenerate} className="surface glass" style={{ width: '450px', padding: '40px', borderRadius: '24px', border: '1px solid var(--border-color)', boxShadow: '0 20px 50px rgba(0,0,0,0.4)', position: 'relative' }}>
              <button 
                type="button"
                onClick={() => setShowGenModal(false)} 
                style={{ position: 'absolute', top: '24px', right: '24px', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                 <FileType size={20} />
              </button>
              
              <h2 className="outfit" style={{ fontSize: '24px', marginBottom: '8px' }}>Generate Analysis Report</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '32px' }}>Configure the parameters for your historical data audit.</p>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                 <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>DOCUMENT NAME</label>
                    <input 
                      type="text" 
                      placeholder="e.g. Q4_Revenue_Audit"
                      value={genForm.name}
                      onChange={e => setGenForm({...genForm, name: e.target.value})}
                      style={{ padding: '12px 16px', borderRadius: '12px', background: 'var(--bg-color)', border: '1px solid var(--border-color)', color: 'white', outline: 'none' }}
                    />
                 </div>

                 <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>EXPORT FORMAT</label>
                    <select 
                      value={genForm.type}
                      onChange={e => setGenForm({...genForm, type: e.target.value})}
                      style={{ padding: '12px 16px', borderRadius: '12px', background: 'var(--bg-color)', border: '1px solid var(--border-color)', color: 'white', outline: 'none' }}
                    >
                       <option value="PDF">Portable Document Format (.pdf)</option>
                       <option value="CSV">Comma Separated Values (.csv)</option>
                       <option value="XLSX">Excel Spreadsheet (.xlsx)</option>
                    </select>
                 </div>
              </div>

              <div style={{ marginTop: '40px', display: 'flex', gap: '12px' }}>
                 <button type="button" onClick={() => setShowGenModal(false)} className="btn btn-ghost" style={{ flex: 1, border: '1px solid var(--border-color)' }}>Cancel</button>
                 <button 
                    type="submit"
                    disabled={generating} 
                    className="btn btn-primary" 
                    style={{ flex: 1, display: 'flex', gap: '8px', justifyContent: 'center' }}
                  >
                   {generating ? <RefreshCw size={18} className="spin" /> : <><Archive size={18} /> Compose Report</>}
                 </button>
              </div>
           </form>
        </div>
      )}

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default Reports;
