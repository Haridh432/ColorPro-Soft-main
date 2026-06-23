'use client';
import { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import ColorSwatch from '@/components/ColorSwatch';
import QualityGateBadge from '@/components/QualityGateBadge';
import DeltaEChart from '@/components/DeltaEChart';
import ShadeGroupPanel from '@/components/ShadeGroupPanel';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

function BatchDetailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const batchId = searchParams.get('id');

  const [batch, setBatch] = useState(null);
  const [rolls, setRolls] = useState([]);
  const [shadeGroups, setShadeGroups] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState('');
  const [showAddRolls, setShowAddRolls] = useState(false);
  const [rollInput, setRollInput] = useState('');

  const [manualScanRoll, setManualScanRoll] = useState(null);
  const [manualScanMode, setManualScanMode] = useState('lab'); // 'rgb' or 'lab'
  const [manualData, setManualData] = useState({ v1: 0, v2: 0, v3: 0 });

  const [showClientModal, setShowClientModal] = useState(false);
  const [clientMode, setClientMode] = useState('lab');
  const [clientData, setClientData] = useState({ v1: 0, v2: 0, v3: 0 });

  const [showAdvancedClusteringModal, setShowAdvancedClusteringModal] = useState(false);
  const [clusterMethod, setClusterMethod] = useState('auto');
  const [clusterCount, setClusterCount] = useState('');
  const [clusterEps, setClusterEps] = useState('0.3');

  useEffect(() => {
    loadBatchData();
  }, [batchId]);

  async function loadBatchData() {
    try {
      const [batchData, rollsData] = await Promise.all([
        api.getBatch(batchId),
        api.getBatchRolls(batchId),
      ]);
      setBatch(batchData);
      setRolls(rollsData);

      // Try loading shade groups
      try {
        const groups = await api.getShadeGroups(batchId);
        if (groups.num_groups > 0) setShadeGroups(groups.groups);
      } catch {}
    } catch (err) {
      console.error('Failed to load batch:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddRolls(e) {
    e.preventDefault();
    const nums = rollInput.split(',').map(s => s.trim()).filter(Boolean);
    if (nums.length === 0) return;

    try {
      await api.bulkCreateRolls(batchId, nums);
      setRollInput('');
      setShowAddRolls(false);
      await loadBatchData();
    } catch (err) {
      alert('Failed: ' + err.message);
    }
  }

  async function handleActionClick(actionFn) {
    try {
      const user = await api.getMe();
      if (!user) {
        router.push('/login');
        return;
      }
      actionFn();
    } catch {
      router.push('/login');
    }
  }

  async function handleManualScanSubmit(rollId) {
    try {
      let payload = {};
      if (manualScanMode === 'rgb') {
        payload.rgb = [parseInt(manualData.v1 || 0), parseInt(manualData.v2 || 0), parseInt(manualData.v3 || 0)];
      } else {
        payload.lab = [parseFloat(manualData.v1 || 0), parseFloat(manualData.v2 || 0), parseFloat(manualData.v3 || 0)];
      }
      await api.uploadScan(rollId, payload);
      setManualScanRoll(null);
      setManualData({ v1: 0, v2: 0, v3: 0 });
      await loadBatchData();
    } catch (err) {
      alert("Failed to submit scan: " + (err.message || 'Check your values'));
    }
  }

  async function handleSetClientSubmit(e) {
    e.preventDefault();
    try {
      let payload = {};
      if (clientMode === 'rgb') {
        payload.rgb = [parseInt(clientData.v1 || 0), parseInt(clientData.v2 || 0), parseInt(clientData.v3 || 0)];
      } else {
        payload.lab = [parseFloat(clientData.v1 || 0), parseFloat(clientData.v2 || 0), parseFloat(clientData.v3 || 0)];
      }
      await api.setClientTarget(batchId, payload);
      setShowClientModal(false);
      await loadBatchData();
    } catch (err) {
      alert("Failed to set Client Master: " + (err.message || 'Check values'));
    }
  }

  async function handleClearClientTarget() {
    try {
      await api.setClientTarget(batchId, { rgb: null });
      await loadBatchData();
    } catch (err) {}
  }

  async function handleSetTargetRoll(rollId) {
    try {
      // Toggle off if it's already the target
      if (batch.target_roll === rollId) {
        await api.setTargetRoll(batchId, null);
      } else {
        await api.setTargetRoll(batchId, rollId);
      }
      await loadBatchData();
    } catch (err) {
      alert("Failed to assign internal target: " + err.message);
    }
  }

  async function handleRunGate() {
    setProcessing('gate');
    try {
      await api.runComparison(batchId, 'CIEDE2000');
      await api.runQualityGate(batchId);
      await loadBatchData();
    } catch (err) {
      alert('Quality gate failed: ' + err.message);
    } finally {
      setProcessing('');
    }
  }

  async function handleRunClustering() {
    setShowAdvancedClusteringModal(true);
  }

  async function submitAdvancedClustering(e) {
    e.preventDefault();
    setProcessing('cluster');
    setShowAdvancedClusteringModal(false);
    try {
      const result = await api.runAdvancedClustering(batchId, {
        method: clusterMethod,
        n_clusters: clusterCount ? parseInt(clusterCount) : null,
        eps: parseFloat(clusterEps)
      });
      setShadeGroups(result.groups);
      await loadBatchData();
    } catch (err) {
      alert('Advanced clustering failed: ' + err.message);
    } finally {
      setProcessing('');
    }
  }

  async function handleSimulateScans() {
    setProcessing('simulate');
    try {
      await api.simulateScans(batchId);
      await loadBatchData();
    } catch (err) {
      alert('Failed to simulate scans: ' + err.message);
    } finally {
      setProcessing('');
    }
  }

  async function handleGenerateReport() {
    setProcessing('report');
    try {
      const report = await api.generateReport(batchId);
      // Download PDF via the dedicated endpoint
      if (report.id) {
        try {
          const blob = await api.downloadReportPdf(report.id);
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `colorpro_${batch.name}_report.pdf`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          window.URL.revokeObjectURL(url);
        } catch {
          // Fallback: open the pdf_url directly
          if (report.pdf_url) {
            window.open(report.pdf_url, '_blank');
          }
        }
      }
      alert('Report generated and downloaded!');
    } catch (err) {
      alert('Report generation failed: ' + err.message);
    } finally {
      setProcessing('');
    }
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <main className="max-w-7xl mx-auto px-6 pt-24">
          <div className="text-center py-20 text-slate-500">Loading batch details...</div>
        </main>
      </>
    );
  }

  if (!batch) {
    return (
      <>
        <Navbar />
        <main className="max-w-7xl mx-auto px-6 pt-24">
          <div className="text-center py-20 text-red-400">Batch not found</div>
        </main>
      </>
    );
  }

  // Group rolls by status
  const acceptedRolls = rolls.filter(r => r.status === 'accepted');
  const warningRolls = rolls.filter(r => r.status === 'warning');
  const rejectedRolls = rolls.filter(r => r.status === 'rejected');
  const pendingRolls = rolls.filter(r => r.status === 'pending');
  const scannedRolls = rolls.filter(r => r.status === 'scanned');

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 pt-24 pb-12">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">{batch.name}</h1>
            {batch.description && <p className="text-slate-400 mt-1">{batch.description}</p>}
            <p className="text-sm text-slate-500 mt-2">
              Created {new Date(batch.created_at).toLocaleDateString()}
            </p>
            
            {/* Targets Header */}
            <div className="flex items-center gap-6 mt-4 p-3 bg-slate-900/50 rounded-lg border border-slate-800">
              {/* Client Master */}
              <div className="flex items-center gap-3">
                {batch.client_l !== null ? (
                  <>
                    <ColorSwatch rgb={[batch.client_r, batch.client_g, batch.client_b_rgb]} size={32} />
                    <div>
                      <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">Client Master</div>
                      <div className="text-xs font-mono text-slate-300">L:{batch.client_l?.toFixed(1)} a:{batch.client_a?.toFixed(1)} b:{batch.client_b?.toFixed(1)}</div>
                    </div>
                    <button onClick={handleClearClientTarget} className="text-slate-500 hover:text-red-400 ml-2">✕</button>
                  </>
                ) : (
                  <button onClick={() => setShowClientModal(true)} className="text-sm font-semibold text-blue-400 hover:text-blue-300">
                    + Set Client Shade
                  </button>
                )}
              </div>

              {/* Internal Target Roll */}
              <div className="pl-6 border-l border-slate-800 flex items-center gap-3">
                {batch.target_roll ? (
                  <>
                    {/* Look up the roll details */}
                    {(() => {
                        const tr = rolls.find(r => r.id === batch.target_roll);
                        if (!tr) return <span className="text-slate-500 text-xs">Target Roll Not Found</span>;
                        return (
                          <>
                            <ColorSwatch rgb={tr.avg_rgb} size={32} />
                            <div>
                               <div className="text-[10px] text-amber-400 font-bold uppercase tracking-wider">Target Roll</div>
                               <div className="text-xs font-mono text-slate-300">Roll {tr.roll_number}</div>
                            </div>
                            {batch.client_l !== null && tr.avg_l !== null && (
                               <div className="ml-2 px-2 py-1 bg-slate-800 rounded text-xs font-mono">
                                  ΔE {(
                                     Math.sqrt(
                                        Math.pow(batch.client_l - tr.avg_l, 2) +
                                        Math.pow(batch.client_a - tr.avg_a, 2) +
                                        Math.pow(batch.client_b - tr.avg_b, 2)
                                     )
                                  ).toFixed(2)}
                               </div>
                            )}
                          </>
                        );
                    })()}
                  </>
                ) : (
                  <div className="text-sm text-slate-500 font-medium italic">No Internal Roll Assigned</div>
                )}
              </div>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => handleActionClick(() => setShowAddRolls(!showAddRolls))}
              className="btn-secondary"
            >
              + Add Rolls
            </button>
            <button
              onClick={() => handleActionClick(handleSimulateScans)}
              className="btn-secondary"
              disabled={!!processing}
            >
              {processing === 'simulate' ? '⟳ Simulating...' : '🤖 Simulate Scans'}
            </button>
            <button
              onClick={() => handleActionClick(handleRunGate)}
              className="btn-primary"
              disabled={!!processing}
            >
              {processing === 'gate' ? '⟳ Running...' : '🔍 Quality Gate'}
            </button>
            <button
              onClick={() => handleActionClick(handleRunClustering)}
              className="btn-secondary"
              disabled={!!processing}
            >
              {processing === 'cluster' ? '⟳ Running...' : '🧬 Advanced Clustering'}
            </button>
            <button
              onClick={() => handleActionClick(handleGenerateReport)}
              className="btn-secondary"
              disabled={!!processing}
            >
              {processing === 'report' ? '⟳ Generating...' : '📄 Report'}
            </button>
          </div>
        </div>

        {/* Add Rolls Form */}
        {showAddRolls && (
          <div className="glass-card p-6 mb-6 animate-fade-in" style={{ cursor: 'default' }}>
            <form onSubmit={handleAddRolls} className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm text-slate-400 mb-2">
                  Roll Numbers (comma separated)
                </label>
                <input
                  className="input-field"
                  placeholder="R-001, R-002, R-003, ..."
                  value={rollInput}
                  onChange={e => setRollInput(e.target.value)}
                  autoFocus
                />
              </div>
              <button type="submit" className="btn-primary">Add</button>
              <button type="button" className="btn-secondary" onClick={() => setShowAddRolls(false)}>
                Cancel
              </button>
            </form>
          </div>
        )}

        {/* Set Client Target Modal inline */}
        {showClientModal && (
          <div className="glass-card p-6 mb-6 animate-fade-in border-blue-500/30" style={{ cursor: 'default' }}>
            <h3 className="text-blue-400 font-semibold mb-4">Set Client Master Shade</h3>
            <form onSubmit={handleSetClientSubmit} className="flex gap-4 items-end">
              <div>
                <div className="flex items-center gap-2 mb-2">
                    <button type="button" onClick={() => { setClientMode('rgb'); setClientData({v1:0, v2:0, v3:0}); }} className={`text-[10px] uppercase font-bold ${clientMode === 'rgb' ? 'text-blue-400' : 'text-slate-500'}`}>RGB</button>
                    <span className="text-slate-600">|</span>
                    <button type="button" onClick={() => { setClientMode('lab'); setClientData({v1:0, v2:0, v3:0}); }} className={`text-[10px] uppercase font-bold ${clientMode === 'lab' ? 'text-blue-400' : 'text-slate-500'}`}>LAB</button>
                </div>
                <div className="flex gap-2">
                  <input type="number" step="any" min={clientMode === 'rgb' ? 0 : undefined} max={clientMode === 'rgb' ? 255 : undefined} className="input-field w-20 h-10 px-2 py-0 text-center" placeholder={clientMode === 'rgb' ? 'R' : 'L*'} value={clientData.v1} onChange={e => setClientData({...clientData, v1: e.target.value})} required />
                  <input type="number" step="any" min={clientMode === 'rgb' ? 0 : undefined} max={clientMode === 'rgb' ? 255 : undefined} className="input-field w-20 h-10 px-2 py-0 text-center" placeholder={clientMode === 'rgb' ? 'G' : 'a*'} value={clientData.v2} onChange={e => setClientData({...clientData, v2: e.target.value})} required />
                  <input type="number" step="any" min={clientMode === 'rgb' ? 0 : undefined} max={clientMode === 'rgb' ? 255 : undefined} className="input-field w-20 h-10 px-2 py-0 text-center" placeholder={clientMode === 'rgb' ? 'B' : 'b*'} value={clientData.v3} onChange={e => setClientData({...clientData, v3: e.target.value})} required />
                </div>
              </div>
              <button type="submit" className="btn-primary h-10">Save Master</button>
              <button type="button" className="btn-secondary h-10" onClick={() => setShowClientModal(false)}>
                Cancel
              </button>
            </form>
          </div>
        )}

        {/* Advanced Clustering Modal inline */}
        {showAdvancedClusteringModal && (
          <div className="glass-card p-6 mb-6 animate-fade-in border-purple-500/30" style={{ cursor: 'default' }}>
            <h3 className="text-purple-400 font-semibold mb-4">Advanced Clustering Parameters</h3>
            <form onSubmit={submitAdvancedClustering} className="flex gap-4 items-end flex-wrap">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Method</label>
                <select 
                  className="input-field h-10 w-32" 
                  value={clusterMethod} 
                  onChange={e => setClusterMethod(e.target.value)}
                >
                  <option value="auto">Auto</option>
                  <option value="kmeans">K-Means</option>
                  <option value="dbscan">DBSCAN</option>
                </select>
              </div>
              
              {clusterMethod === 'kmeans' && (
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Number of Clusters (K)</label>
                  <input 
                    type="number" 
                    min="1" 
                    className="input-field h-10 w-32" 
                    placeholder="Auto"
                    value={clusterCount} 
                    onChange={e => setClusterCount(e.target.value)} 
                  />
                </div>
              )}

              {clusterMethod === 'dbscan' && (
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Epsilon (ΔE max)</label>
                  <input 
                    type="number" 
                    step="0.1" 
                    min="0.1" 
                    className="input-field h-10 w-32" 
                    value={clusterEps} 
                    onChange={e => setClusterEps(e.target.value)} 
                  />
                </div>
              )}

              <button type="submit" className="btn-primary h-10 ml-auto">Run Cluster</button>
              <button type="button" className="btn-secondary h-10" onClick={() => setShowAdvancedClusteringModal(false)}>
                Cancel
              </button>
            </form>
          </div>
        )}

        {/* Quality Gate Summary */}
        <div className="grid grid-cols-5 gap-4 mb-8">
          {[
            { label: 'Total', count: rolls.length, color: 'text-white' },
            { label: 'Accepted', count: acceptedRolls.length, color: 'text-green-400' },
            { label: 'Warning', count: warningRolls.length, color: 'text-amber-400' },
            { label: 'Rejected', count: rejectedRolls.length, color: 'text-red-400' },
            { label: 'Pending', count: pendingRolls.length + scannedRolls.length, color: 'text-slate-400' },
          ].map(stat => (
            <div
              key={stat.label}
              className="glass-card p-4 text-center"
              style={{ cursor: 'default' }}
            >
              <div className={`text-2xl font-bold ${stat.color}`}>{stat.count}</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider mt-1">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Roll Table */}
        <div className="glass-card p-6 mb-8 overflow-x-auto" style={{ cursor: 'default' }}>
          <h2 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">
            All Rolls
          </h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">Roll #</th>
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">Color</th>
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">L*</th>
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">a*</th>
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">b*</th>
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">ΔE</th>
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">Status</th>
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">Group</th>
                <th className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase">Held</th>
                <th className="text-right py-3 px-3 text-slate-500 font-medium text-xs uppercase">Action</th>
              </tr>
            </thead>
            <tbody>
              {rolls.map(roll => (
                <tr key={roll.id} className="border-b border-slate-800 hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-3 font-medium text-white">{roll.roll_number}</td>
                  <td className="py-3 px-3">
                    <ColorSwatch rgb={roll.avg_rgb} size={28} />
                  </td>
                  <td className="py-3 px-3 text-slate-300 font-mono text-xs">
                    {roll.avg_l?.toFixed(2) || '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-300 font-mono text-xs">
                    {roll.avg_a?.toFixed(2) || '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-300 font-mono text-xs">
                    {roll.avg_b?.toFixed(2) || '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-300 font-mono text-xs">
                    {roll.delta_e?.toFixed(4) || '—'}
                  </td>
                  <td className="py-3 px-3">
                    <QualityGateBadge status={roll.status} />
                  </td>
                  <td className="py-3 px-3 text-slate-400 text-xs">
                    {roll.shade_group ? `Group ${roll.shade_group}` : '—'}
                  </td>
                  <td className="py-3 px-3">
                    {roll.is_held && <span className="text-amber-400 text-xs">⏸ Held</span>}
                  </td>
                  <td className="py-3 px-3 text-right">
                    {manualScanRoll === roll.id ? (
                      <div className="flex flex-col items-end gap-2">
                        <div className="flex items-center gap-2">
                          <button onClick={() => { setManualScanMode('rgb'); setManualData({v1:0, v2:0, v3:0}); }} className={`text-[10px] uppercase font-bold ${manualScanMode === 'rgb' ? 'text-blue-400' : 'text-slate-500'}`}>RGB</button>
                          <span className="text-slate-600">|</span>
                          <button onClick={() => { setManualScanMode('lab'); setManualData({v1:0, v2:0, v3:0}); }} className={`text-[10px] uppercase font-bold ${manualScanMode === 'lab' ? 'text-blue-400' : 'text-slate-500'}`}>LAB</button>
                        </div>
                        <div className="flex items-center justify-end gap-1">
                          <input type="number" step="any" min={manualScanMode === 'rgb' ? 0 : undefined} max={manualScanMode === 'rgb' ? 255 : undefined} className="input-field w-14 h-7 px-1 py-0 text-xs text-center" placeholder={manualScanMode === 'rgb' ? 'R' : 'L*'} value={manualData.v1} onChange={e => setManualData({...manualData, v1: e.target.value})} />
                          <input type="number" step="any" min={manualScanMode === 'rgb' ? 0 : undefined} max={manualScanMode === 'rgb' ? 255 : undefined} className="input-field w-14 h-7 px-1 py-0 text-xs text-center" placeholder={manualScanMode === 'rgb' ? 'G' : 'a*'} value={manualData.v2} onChange={e => setManualData({...manualData, v2: e.target.value})} />
                          <input type="number" step="any" min={manualScanMode === 'rgb' ? 0 : undefined} max={manualScanMode === 'rgb' ? 255 : undefined} className="input-field w-14 h-7 px-1 py-0 text-xs text-center" placeholder={manualScanMode === 'rgb' ? 'B' : 'b*'} value={manualData.v3} onChange={e => setManualData({...manualData, v3: e.target.value})} />
                          <button onClick={() => handleActionClick(() => handleManualScanSubmit(roll.id))} className="text-emerald-400 font-bold ml-1 hover:text-emerald-300">✓</button>
                          <button onClick={() => setManualScanRoll(null)} className="text-slate-400 ml-1 hover:text-slate-300">✕</button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-end gap-3">
                        <button onClick={() => handleActionClick(() => handleSetTargetRoll(roll.id))} className="text-xs text-amber-500 hover:text-amber-400" title={batch.target_roll === roll.id ? "Unassign Target" : "Set as Target Roll"}>
                          {batch.target_roll === roll.id ? '★ Target' : '☆ Make Target'}
                        </button>
                        <button 
                          onClick={() => handleActionClick(() => {
                            setManualScanRoll(roll.id);
                            setManualData({v1: 0, v2: 0, v3: 0});
                          })}
                          className="text-xs text-blue-400 hover:text-blue-300 underline"
                        >
                          + Add Scan
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Charts & Groups */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DeltaEChart rolls={rolls} />
          <ShadeGroupPanel groups={shadeGroups} />
        </div>
      </main>
    </>
  );
}

export default function BatchDetailPage() {
  return (
    <Suspense fallback={<div className="text-center p-12 text-slate-400">Loading Dashboard...</div>}>
      <BatchDetailContent />
    </Suspense>
  );
}
