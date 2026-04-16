import React, { useState, useMemo } from 'react';
import { 
  Library as LibraryIcon, Search, Tag, Calendar, 
  ChevronRight, Bookmark, X, Download, Share2, 
  Trash2, Plus, LineChart as ChartIcon, Eye
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  BarChart, Bar, Cell 
} from 'recharts';

const MOCK_INSIGHTS = [
  { 
    id: 1, 
    title: 'Q1 Revenue Recovery', 
    summary: 'Analysis of organic channel growth following the January decline. Strong performance in Ceramic Vase categories.',
    tags: ['Revenue', 'Growth'], 
    date: 'Apr 10, 2024',
    content: {
      text: "The recovery was driven primarily by a 25% increase in repeat customers in the 'Decor' category. Organic traffic stabilized by week 3 and saw a late-quarter surge due to favorable SEO indexing on new SKU pages.",
      chartType: 'line',
      data: [
         { name: 'Jan', val: 12000 }, { name: 'Feb', val: 15500 }, { name: 'Mar', val: 22000 }, { name: 'Apr', val: 24000 }
      ]
    }
  },
  { 
    id: 2, 
    title: 'Inventory Alert Audit', 
    summary: 'Summary of threshold breaches for Traditional Kilns. Lead times from supplier Fakhoury have increased by 20%.',
    tags: ['Supply Chain', 'Audit'], 
    date: 'Apr 12, 2024',
    content: {
      text: "Current inventory levels for SKU-102 are at critical minimums. The audit suggests shifting 30% of order volume to local Warehouse B to mitigate the shipping delays from the main port.",
      chartType: 'bar',
      data: [
        { name: 'Stock', val: 45 }, { name: 'Lead Time', val: 80 }, { name: 'Orders', val: 120 }
      ]
    }
  },
  { 
    id: 3, 
    title: 'Flash Sale Performance', 
    summary: 'Conversion analysis from the Summer Flash Sale. Paid Ads provided 3:1 ROI.',
    tags: ['Marketing', 'ROI'], 
    date: 'Mar 28, 2024',
    content: {
      text: "User acquisition costs were significantly lower ($2.40) during the first 6 hours of the sale. Recommend front-loading next campaign budget into initial phase.",
      chartType: 'bar',
      data: [
        { name: 'Paid', val: 45000 }, { name: 'Organic', val: 12000 }, { name: 'Referral', val: 8000 }
      ]
    }
  }
];

const Library = () => {
  const [search, setSearch] = useState('');
  const [selectedInsight, setSelectedInsight] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const filteredInsights = useMemo(() => {
    return MOCK_INSIGHTS.filter(item => 
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.tags.some(t => t.toLowerCase().includes(search.toLowerCase()))
    );
  }, [search]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* ── Header & Action ── */}
      <div className="surface glass" style={{ padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
           <h1 className="outfit" style={{ fontSize: '28px', marginBottom: '4px' }}>Knowledge Library</h1>
           <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>A repository of archived insights and analytical deep-dives.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAddModal(true)} style={{ display: 'flex', gap: '8px' }}>
           <Plus size={18} /> Add Entry
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
        
        {/* ── Sidebar: List ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
           <div style={{ position: 'relative' }}>
              <input 
                type="text" 
                placeholder="Search archives..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{
                  width: '100%', padding: '12px 16px 12px 40px', borderRadius: '12px',
                  background: 'var(--surface-color)', border: '1px solid var(--border-color)',
                  color: 'var(--text-primary)', outline: 'none'
                }}
              />
              <Search size={16} color="var(--text-secondary)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
           </div>

           <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {filteredInsights.map(insight => (
                <div 
                  key={insight.id}
                  onClick={() => setSelectedInsight(insight)}
                  className="surface hoverable"
                  style={{
                    padding: '16px', cursor: 'pointer', border: selectedInsight?.id === insight.id ? '1px solid var(--accent-color)' : '1px solid var(--border-color)',
                    background: selectedInsight?.id === insight.id ? 'var(--surface-hover)' : 'var(--surface-color)'
                  }}
                >
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '8px' }}>{insight.date}</div>
                  <h4 style={{ fontSize: '15px', marginBottom: '8px' }}>{insight.title}</h4>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                     {insight.tags.map(tag => (
                       <span key={tag} style={{ fontSize: '10px', padding: '2px 6px', background: 'var(--bg-color)', borderRadius: '4px', color: 'var(--accent-color)', border: '1px solid var(--border-color)' }}>{tag}</span>
                     ))}
                  </div>
                </div>
              ))}
           </div>
        </div>

        {/* ── Main View: Detail ── */}
        <div style={{ minHeight: '600px' }}>
          {selectedInsight ? (
            <div className="surface" style={{ padding: '40px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h2 className="outfit" style={{ fontSize: '32px', marginBottom: '8px' }}>{selectedInsight.title}</h2>
                    <div style={{ display: 'flex', gap: '16px', color: 'var(--text-secondary)', fontSize: '13px' }}>
                       <span>Author: AI Engine</span>
                       <span>Date: {selectedInsight.date}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button className="btn btn-ghost" style={{ border: '1px solid var(--border-color)' }}><Share2 size={18} /></button>
                    <button className="btn btn-ghost" style={{ border: '1px solid var(--border-color)' }}><Download size={18} /></button>
                  </div>
               </div>

               <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', alignItems: 'center' }}>
                  <div style={{ height: '300px', background: 'var(--bg-color)', borderRadius: '20px', padding: '20px', border: '1px solid var(--border-color)' }}>
                     <ResponsiveContainer width="100%" height="100%">
                        {selectedInsight.content.chartType === 'line' ? (
                          <LineChart data={selectedInsight.content.data}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                            <XAxis dataKey="name" axisLine={false} tickLine={false} />
                            <YAxis axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)' }} />
                            <Line type="monotone" dataKey="val" stroke="var(--accent-color)" strokeWidth={3} dot={{r: 4}} />
                          </LineChart>
                        ) : (
                          <BarChart data={selectedInsight.content.data}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                            <XAxis dataKey="name" axisLine={false} tickLine={false} />
                            <YAxis axisLine={false} tickLine={false} />
                            <Bar dataKey="val" fill="var(--accent-color)" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        )}
                     </ResponsiveContainer>
                  </div>
                  <div>
                     <h3 className="outfit" style={{ fontSize: '18px', marginBottom: '16px' }}>Summary Insight</h3>
                     <p style={{ color: 'var(--text-secondary)', fontSize: '15px', lineHeight: '1.8' }}>
                       {selectedInsight.content.text}
                     </p>
                  </div>
               </div>

               <div style={{ marginTop: '20px', padding: '24px', background: 'var(--surface-hover)', borderRadius: '16px', display: 'flex', gap: '20px', alignItems: 'center' }}>
                  <Bookmark size={24} color="var(--accent-color)" />
                  <div style={{ flex: 1 }}>
                     <h4 style={{ fontSize: '14px', marginBottom: '4px' }}>Expert Note</h4>
                     <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>This finding is consistent with historical trend #804 regarding seasonal ceramic demand. Recommend monitoring SKU-302 closely.</p>
                  </div>
                  <button className="btn btn-ghost" style={{ border: '1px solid var(--border-color)' }}>Archive Policy</button>
               </div>
            </div>
          ) : (
            <div className="surface" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', border: '2px dashed var(--border-color)' }}>
               <LibraryIcon size={64} style={{ opacity: 0.1, marginBottom: '24px' }} />
               <p className="outfit" style={{ fontSize: '20px' }}>Select an archive to view findings</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Add Modal ── */}
      {showAddModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="surface" style={{ width: '400px', padding: '32px', textAlign: 'center' }}>
             <h2 className="outfit" style={{ fontSize: '22px', marginBottom: '16px' }}>Store New Insight</h2>
             <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>The "AI Analyst" usually populates these automatically, but you can manually archive a session state.</p>
             <button onClick={() => setShowAddModal(false)} className="btn btn-primary" style={{ width: '100%' }}>Confirm Archive</button>
          </div>
        </div>
      )}

    </div>
  );
};

export default Library;
