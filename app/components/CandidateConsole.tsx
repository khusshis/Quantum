import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Download, Cpu, HardDrive, Clock, CheckCircle2, AlertTriangle, Filter, Search, ChevronDown, ChevronUp } from 'lucide-react';
import { CandidateDrawer } from './CandidateDrawer';
import { FEATURE_KEYS, FEATURE_COLORS, formatFeatureName } from './FeatureConstants';

const FilterPopover = ({ label, value, onChange, min, max, step, formatValue, anyValue }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tempValue, setTempValue] = useState(value);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    setTempValue(value);
  }, [value]);

  const handleApply = (val: number) => {
    setTempValue(val);
    onChange(val);
  };

  return (
    <div className="relative" ref={popoverRef}>
      <div 
        className="flex items-center gap-2 cursor-pointer hover:bg-[#27272A] px-2 py-1.5 rounded transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="text-[#71717A]">{label}:</span>
        <span className="text-[#EDEDED] font-medium">{value === anyValue ? 'Any' : formatValue(value)}</span>
      </div>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-56 bg-[#121212] border border-[#27272A] rounded-lg shadow-2xl p-4 z-50">
          <div className="flex items-center justify-between mb-4">
            <span className="text-[11px] font-mono text-[#A1A1AA] uppercase tracking-wider">{label}</span>
            <input 
              type="text" 
              className="bg-[#0A0A0A] border border-[#27272A] rounded px-2 py-1 text-[#EDEDED] text-[11px] font-mono w-14 text-center outline-none focus:border-[#3B82F6] transition-colors"
              value={tempValue === anyValue ? '' : tempValue}
              placeholder="Any"
              onChange={(e) => {
                const val = e.target.value === '' ? anyValue : Number(e.target.value);
                if (!isNaN(val)) handleApply(val);
              }}
            />
          </div>
          
          <div className="relative pt-1 pb-2">
            <input 
              type="range" 
              min={min} 
              max={max} 
              step={step}
              value={tempValue === anyValue ? max : tempValue}
              onChange={(e) => {
                const val = Number(e.target.value);
                handleApply(val === max ? anyValue : val);
              }}
              className="w-full h-1 bg-[#27272A] rounded-lg appearance-none cursor-pointer outline-none custom-slider-thumb"
              style={{
                background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${((tempValue === anyValue ? max : tempValue) - min) / (max - min) * 100}%, #27272A ${((tempValue === anyValue ? max : tempValue) - min) / (max - min) * 100}%, #27272A 100%)`
              }}
            />
          </div>
          
          <div className="flex justify-between text-[10px] text-[#71717A] mt-1 font-mono">
            <span>{min}</span>
            <span>Any</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default function CandidateConsole() {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [benchmark, setBenchmark] = useState<any>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<any | null>(null);
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);

  // Filters
  const [filterHoneypot, setFilterHoneypot] = useState<'all' | 'safe' | 'flagged'>('all');
  const [filterNotice, setFilterNotice] = useState<'all' | '30' | '60' | '90'>('all');
  const [filterTitle, setFilterTitle] = useState<string>('all');
  const [filterMinExp, setFilterMinExp] = useState<number>(0);
  const [filterMaxSalary, setFilterMaxSalary] = useState<number>(200);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<{key: string, direction: 'asc' | 'desc'} | null>(null);

  useEffect(() => {
    fetch('/ranked_candidates.json?t=' + new Date().getTime())
      .then(res => res.json())
      .then(data => setCandidates(data))
      .catch(err => console.error("Error loading candidates:", err));

    fetch('/benchmark_report.json?t=' + new Date().getTime())
      .then(res => res.json())
      .then(data => setBenchmark(data))
      .catch(err => console.error("Error loading benchmark:", err));
  }, []);

  const exportCSV = () => {
    if (!candidates.length) return;
    const header = "candidate_id,rank,score,reasoning\n";
    const rows = candidates.map(c => `"${c.candidate_id}",${c.rank},${c.score},"${c.reasoning.replace(/"/g, '""')}"`);
    const csvContent = "data:text/csv;charset=utf-8," + header + rows.join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "submission.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const processedCandidates = useMemo(() => {
    let filtered = [...candidates];
    
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      filtered = filtered.filter(c => 
        (c.name && c.name.toLowerCase().includes(q)) ||
        (c.title && c.title.toLowerCase().includes(q)) ||
        (c.company && c.company.toLowerCase().includes(q)) ||
        (c.candidate_id && c.candidate_id.toLowerCase().includes(q))
      );
    }

    if (filterTitle !== 'all') {
      filtered = filtered.filter(c => c.title === filterTitle);
    }
    
    if (filterHoneypot === 'safe') {
      filtered = filtered.filter(c => (c.features.honeypot_suspicion_score || 0) < 0.5);
    } else if (filterHoneypot === 'flagged') {
      filtered = filtered.filter(c => (c.features.honeypot_suspicion_score || 0) >= 0.5);
    }

    if (filterNotice !== 'all') {
      filtered = filtered.filter(c => {
        if (c.notice_period_days === undefined) return false;
        if (filterNotice === '30') return c.notice_period_days <= 30;
        if (filterNotice === '60') return c.notice_period_days <= 60;
        if (filterNotice === '90') return c.notice_period_days > 60;
        return true;
      });
    }

    if (filterMinExp > 0) {
      filtered = filtered.filter(c => (c.yoe || 0) >= filterMinExp);
    }
    
    if (filterMaxSalary < 200) {
      filtered = filtered.filter(c => {
        if (!c.expected_salary || !c.expected_salary.max) return true;
        return c.expected_salary.max <= filterMaxSalary;
      });
    }

    if (sortConfig) {
      filtered.sort((a, b) => {
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];
        
        // Handle nested features
        if (sortConfig.key.startsWith('features.')) {
          const fKey = sortConfig.key.split('.')[1];
          aVal = a.features[fKey] || 0;
          bVal = b.features[fKey] || 0;
        }

        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [candidates, filterHoneypot, filterNotice, filterTitle, searchTerm, sortConfig, filterMinExp, filterMaxSalary]);

  const requestSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) return null;
    return sortConfig.direction === 'asc' ? <ChevronUp size={12} className="inline ml-1" /> : <ChevronDown size={12} className="inline ml-1" />;
  };

  const top10 = candidates.slice(0, 10);
  const runnersUp = candidates.slice(10, 15);

  const uniqueTitles = useMemo(() => {
    const titles = new Set<string>();
    candidates.forEach(c => {
      if (c.title) titles.add(c.title);
    });
    return Array.from(titles).sort();
  }, [candidates]);

  return (
    <div className="flex flex-col h-screen bg-[#0A0A0A] text-[#EDEDED] font-sans overflow-hidden">
      
      {/* Header Panel */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-[#27272A] bg-[#0A0A0A]">
        <div>
          <h1 className="text-xl font-medium tracking-tight flex items-center gap-2">
            <span className="text-[#A1A1AA]">Quantum</span> / Candidate Intelligence
          </h1>
          <div className="flex items-center gap-4 mt-2 text-[11px] text-[#71717A] font-mono tracking-wider">
            <span>POOL: 100,000</span>
            <span className="text-[#EDEDED]">SHORTLIST: {candidates.length}</span>
            {benchmark && <span>LAST RUN: {new Date(benchmark.timestamp * 1000).toLocaleString()}</span>}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono font-medium text-[#10B981] bg-[#10B981]/10 rounded border border-[#10B981]/20">
            <CheckCircle2 size={14} />
            <span>0 EXTERNAL API CALLS</span>
          </div>
          <button onClick={exportCSV} className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono font-medium text-white bg-[#27272A] hover:bg-[#3F3F46] border border-[#3F3F46] rounded transition-colors">
            <Download size={14} />
            EXPORT CSV
          </button>
        </div>
      </header>

      {/* Filter Bar */}
      <div className="flex items-center gap-6 px-6 py-2 border-b border-[#27272A] bg-[#121212] text-xs font-mono">
        <div className="flex items-center gap-2 text-[#A1A1AA]">
          <Filter size={14} />
          <span>FILTERS</span>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-[#71717A]">Honeypot:</span>
          <select 
            value={filterHoneypot}
            onChange={(e) => setFilterHoneypot(e.target.value as any)}
            className="bg-[#0A0A0A] border border-[#27272A] text-[#EDEDED] rounded px-2 py-1 outline-none focus:border-[#52525B]"
          >
            <option value="all">All Candidates</option>
            <option value="safe">Safe Only</option>
            <option value="flagged">Flagged Only</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[#71717A]">Notice:</span>
          <select 
            value={filterNotice}
            onChange={(e) => setFilterNotice(e.target.value as any)}
            className="bg-[#0A0A0A] border border-[#27272A] text-[#EDEDED] rounded px-2 py-1 outline-none focus:border-[#52525B]"
          >
            <option value="all">Any</option>
            <option value="30">≤ 30 days</option>
            <option value="60">≤ 60 days</option>
            <option value="90">&gt; 60 days</option>
          </select>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-[#71717A]">Role:</span>
          <select 
            value={filterTitle}
            onChange={(e) => setFilterTitle(e.target.value)}
            className="bg-[#0A0A0A] border border-[#27272A] text-[#EDEDED] rounded px-2 py-1 outline-none focus:border-[#52525B] max-w-[120px]"
          >
            <option value="all">All Roles</option>
            {uniqueTitles.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        
        <FilterPopover 
          label="Min YOE" 
          value={filterMinExp} 
          onChange={setFilterMinExp}
          min={0} max={20} step={1}
          anyValue={0}
          formatValue={(v: number) => `${v}+ yrs`}
        />

        <FilterPopover 
          label="Max Salary" 
          value={filterMaxSalary} 
          onChange={setFilterMaxSalary}
          min={5} max={100} step={5}
          anyValue={200}
          formatValue={(v: number) => `≤ ₹${v}L`}
        />
        
        <div className="ml-auto flex items-center gap-4">
          <div className="relative">
            <Search size={14} className="absolute left-2 top-1.5 text-[#71717A]" />
            <input 
              type="text" 
              placeholder="Search ID, name, co..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-[#0A0A0A] border border-[#27272A] text-[#EDEDED] rounded pl-7 pr-2 py-1 text-xs outline-none focus:border-[#52525B] w-[180px]"
            />
          </div>
          <span className="text-[#71717A]">
            Showing {processedCandidates.length} results
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden flex relative">
        <main className="flex-1 overflow-y-auto no-scrollbar flex flex-col">
          <div className="flex-1">
            <table className="w-full text-sm text-left border-collapse">
              <thead className="text-[10px] uppercase text-[#71717A] bg-[#0A0A0A] sticky top-0 z-10 font-mono tracking-wider border-b border-[#27272A]">
                <tr>
                  <th className="px-6 py-2.5 font-medium cursor-pointer hover:text-[#EDEDED]" onClick={() => requestSort('rank')}>
                    Rank {getSortIcon('rank')}
                  </th>
                  <th className="px-6 py-2.5 font-medium cursor-pointer hover:text-[#EDEDED]" onClick={() => requestSort('candidate_id')}>
                    Candidate {getSortIcon('candidate_id')}
                  </th>
                  <th className="px-6 py-2.5 font-medium">Profile Overview</th>
                  <th className="px-6 py-2.5 font-medium">Notice</th>
                  <th className="px-6 py-2.5 font-medium">Exp & Salary</th>
                  <th className="px-6 py-2.5 font-medium text-right cursor-pointer hover:text-[#EDEDED]" onClick={() => requestSort('score')}>
                    Rating (/100) {getSortIcon('score')}
                  </th>
                  <th className="px-6 py-2.5 font-medium w-48">Hiring Signals</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#27272A]">
                {processedCandidates.map((c) => (
                  <tr 
                    key={c.candidate_id} 
                    onClick={() => setSelectedCandidate(c)}
                    className={`cursor-pointer transition-colors feature-row group ${selectedCandidate?.candidate_id === c.candidate_id ? 'bg-[#18181B]' : 'hover:bg-[#121212]'}`}
                  >
                    <td className="px-6 py-3 font-mono text-[#A1A1AA] text-xs">
                      {c.rank.toString().padStart(3, '0')}
                    </td>
                    <td className="px-6 py-3 font-mono text-xs opacity-80 group-hover:opacity-100 transition-opacity">
                      <div className="text-[#EDEDED] font-medium font-sans text-sm flex items-center gap-2">
                        {c.name}
                        {c.redrob_signals?.recruiter_response_rate > 0.90 && c.redrob_signals?.interview_completion_rate > 0.90 && (
                          <div className="relative group cursor-help flex items-center justify-center">
                            <div className="w-1.5 h-1.5 rounded-full bg-[#EAB308] shadow-[0_0_6px_rgba(234,179,8,0.6)]"></div>
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 bg-[#27272A] border border-[#3F3F46] text-[#EDEDED] text-[9px] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl font-sans font-normal">
                              ⚡ Fast Mover: &gt;90% Response & Interview Show Rate
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="text-[#71717A] text-[10px]">{c.candidate_id}</div>
                    </td>
                    <td className="px-6 py-3">
                      <div className="font-medium text-[#EDEDED] flex items-center gap-2">
                        {c.title || 'Unknown Title'}
                        {c.notice_period_days !== undefined && c.notice_period_days <= 30 && (
                          <span className="px-1.5 py-0.5 rounded-sm bg-[#10B981]/10 text-[#10B981] text-[9px] font-mono font-bold">FAST JOIN</span>
                        )}
                      </div>
                      <div className="text-xs text-[#71717A] mt-0.5 font-medium">{c.company || 'Unknown Company'}</div>
                      <div className="text-[10px] text-[#A1A1AA] mt-1.5 line-clamp-1 border-l-2 border-[#3F3F46] pl-2 font-mono">
                        {c.preview_reasoning || c.reasoning}
                      </div>
                    </td>
                    <td className="px-6 py-3 font-mono text-[#A1A1AA] text-xs">
                      {c.notice_period_days !== undefined ? `${c.notice_period_days}d` : 'N/A'}
                    </td>
                    <td className="px-6 py-3 font-mono text-[#EDEDED] text-xs">
                      {c.yoe !== undefined ? `${c.yoe} yrs` : 'N/A'}
                      <div className="text-[10px] text-[#71717A] mt-0.5">
                        {c.expected_salary?.min && c.expected_salary?.max 
                          ? `₹${c.expected_salary.min}-${c.expected_salary.max}L` 
                          : 'Negotiable'}
                      </div>
                    </td>
                    <td className="px-6 py-3 text-right font-mono text-[#EDEDED] text-xs">
                      {(c.score * 100).toFixed(2)}
                      {c.features.honeypot_suspicion_score >= 0.5 && (
                        <AlertTriangle size={12} className="inline ml-2 text-[#EF4444]" title="Honeypot Suspicion" />
                      )}
                    </td>
                    <td className="px-6 py-3">
                      <div className="flex flex-col gap-1.5 w-full max-w-[160px] text-[9px] font-mono">
                        <div className="flex items-center justify-between">
                          <span className="text-[#71717A]">Status</span>
                          <span className={c.redrob_signals?.open_to_work_flag ? 'text-[#10B981] font-bold' : 'text-[#A1A1AA]'}>
                            {c.redrob_signals?.open_to_work_flag ? 'Open to Work' : 'Passive'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[#71717A]">Response Rate</span>
                          <span className="text-[#EDEDED]">
                            {c.redrob_signals?.recruiter_response_rate ? `${(c.redrob_signals.recruiter_response_rate * 100).toFixed(0)}%` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[#71717A]">Interview Show</span>
                          <span className="text-[#EDEDED]">
                            {c.redrob_signals?.interview_completion_rate ? `${(c.redrob_signals.interview_completion_rate * 100).toFixed(0)}%` : 'N/A'}
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Contrastive Strip - Styled like a data diff tool */}
          <div className="border-t border-[#27272A] bg-[#0A0A0A] flex flex-col mt-auto shrink-0 relative z-10">
            <div className="px-6 py-2 border-b border-[#27272A] bg-[#121212] flex items-center">
              <span className="text-[10px] text-[#A1A1AA] uppercase tracking-wider font-mono font-bold flex items-center gap-2">
                <Search size={12} /> Contrastive Analysis: Runners-Up
              </span>
              <span className="text-[10px] text-[#71717A] ml-4 font-mono">
                Baseline: Rank {selectedCandidate && selectedCandidate.rank <= 10 ? `#${selectedCandidate.rank}` : '#10 (Cutoff)'}
              </span>
            </div>
            <div className="flex overflow-x-auto no-scrollbar">
              {runnersUp.map(runner => {
                const cutoff = (selectedCandidate && selectedCandidate.rank <= 10) ? selectedCandidate : top10[9];
                let biggestGapKey = '';
                let biggestGap = -9999;
                
                if (cutoff && cutoff.features && runner.features) {
                  Object.keys(cutoff.features).forEach(k => {
                    if (k in runner.features) {
                      const gap = cutoff.features[k] - runner.features[k];
                      if (gap > biggestGap) {
                        biggestGap = gap;
                        biggestGapKey = k;
                      }
                    }
                  });
                }
                
                return (
                <div key={runner.candidate_id} className="flex-shrink-0 w-64 border-r border-[#27272A] p-3 hover:bg-[#121212] transition-colors">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono text-[10px] text-[#71717A]">RANK {runner.rank.toString().padStart(3, '0')}</span>
                    <span className="font-mono text-[10px] text-[#EDEDED]">{(runner.score * 100).toFixed(2)}</span>
                  </div>
                  <div className="text-xs font-medium truncate text-[#EDEDED] mb-2">{runner.title || 'Unknown Title'}</div>
                  
                  <div className="bg-[#18181B] rounded border border-[#27272A] p-2">
                    <div className="text-[9px] text-[#71717A] font-mono uppercase mb-1">Primary Deficit</div>
                    <div className="flex justify-between items-end">
                      <span className="text-[10px] text-[#F87171] font-medium truncate pr-2">
                        {biggestGapKey ? formatFeatureName(biggestGapKey) : 'Low overall signals'}
                      </span>
                      <span className="font-mono text-[10px] text-[#F87171] shrink-0">
                        {biggestGapKey ? `-${biggestGap.toFixed(2)}` : ''}
                      </span>
                    </div>
                  </div>
                </div>
              )})}
            </div>
          </div>
        </main>

        {/* Candidate Detail Drawer */}
        {selectedCandidate && (
          <CandidateDrawer 
            candidate={selectedCandidate} 
            onClose={() => setSelectedCandidate(null)} 
          />
        )}
      </div>

      {/* Footer Panel - Terminal Style */}
      <footer className="flex items-center justify-between px-6 py-1.5 border-t border-[#27272A] bg-[#0A0A0A] text-[10px] font-mono text-[#71717A]">
        <div className="flex gap-6">
          <span className="flex items-center gap-1.5 text-[#EDEDED]"><Cpu size={12} className="text-[#A1A1AA]"/> CPU_RANKING</span>
          <span className="flex items-center gap-1.5"><Clock size={12}/> ELAPSED: {benchmark?.elapsed_seconds?.toFixed(3) || '--'}s</span>
          <span className="flex items-center gap-1.5"><HardDrive size={12}/> PEAK_RSS: {benchmark?.peak_memory_mb?.toFixed(1) || '--'}MB</span>
        </div>
        <div className="flex gap-4">
          <span>PIPELINE: Hybrid BM25/Dense + LightGBM</span>
          <span className="text-[#52525B]">|</span>
          <span>v1.0.0</span>
        </div>
      </footer>
    </div>
  );
}
