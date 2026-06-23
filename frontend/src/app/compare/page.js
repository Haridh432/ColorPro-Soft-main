'use client';
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import ColorSwatch from '@/components/ColorSwatch';
import api from '@/lib/api';

export default function ComparePage() {
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState('');
  const [rolls, setRolls] = useState([]);
  const [roll1, setRoll1] = useState('');
  const [roll2, setRoll2] = useState('');
  const [results, setResults] = useState(null);
  const [allResults, setAllResults] = useState([]);

  useEffect(() => {
    api.getBatches().then(data => setBatches(data.results || data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedBatch) {
      api.getBatchRolls(selectedBatch).then(setRolls).catch(() => {});
      api.getComparisonResults(selectedBatch).then(setAllResults).catch(() => setAllResults([]));
    }
  }, [selectedBatch]);

  const rollMap = {};
  rolls.forEach(r => { rollMap[r.id] = r; });

  const selectedRoll1 = rollMap[roll1];
  const selectedRoll2 = rollMap[roll2];

  // Find specific comparison result
  useEffect(() => {
    if (roll1 && roll2 && allResults.length > 0) {
      const found = allResults.find(
        r => (r.roll_1 === roll1 && r.roll_2 === roll2) ||
             (r.roll_1 === roll2 && r.roll_2 === roll1)
      );
      setResults(found || null);
    } else {
      setResults(null);
    }
  }, [roll1, roll2, allResults]);

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 pt-24 pb-12">
        <h1 className="text-3xl font-bold text-white mb-2">Compare Rolls</h1>
        <p className="text-slate-400 mb-8">Select two rolls to compare their shade difference</p>

        {/* Batch & Roll Selection */}
        <div className="glass-card p-6 mb-8" style={{ cursor: 'default' }}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm text-slate-400 mb-2">Select Batch</label>
              <select
                className="input-field"
                value={selectedBatch}
                onChange={e => { setSelectedBatch(e.target.value); setRoll1(''); setRoll2(''); }}
              >
                <option value="">Choose a batch...</option>
                {batches.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">Roll 1</label>
              <select
                className="input-field"
                value={roll1}
                onChange={e => setRoll1(e.target.value)}
                disabled={!selectedBatch}
              >
                <option value="">Select roll...</option>
                {rolls.filter(r => r.id !== roll2).map(r => (
                  <option key={r.id} value={r.id}>{r.roll_number}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">Roll 2</label>
              <select
                className="input-field"
                value={roll2}
                onChange={e => setRoll2(e.target.value)}
                disabled={!selectedBatch}
              >
                <option value="">Select roll...</option>
                {rolls.filter(r => r.id !== roll1).map(r => (
                  <option key={r.id} value={r.id}>{r.roll_number}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Comparison View */}
        {selectedRoll1 && selectedRoll2 && (
          <div className="animate-fade-in">
            {/* Side-by-side swatches */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* Roll 1 */}
              <div className="glass-card p-6 text-center" style={{ cursor: 'default' }}>
                <h3 className="text-lg font-bold text-white mb-4">{selectedRoll1.roll_number}</h3>
                <div className="flex justify-center mb-4">
                  <ColorSwatch rgb={selectedRoll1.avg_rgb} size={120} />
                </div>
                <div className="space-y-1 text-sm text-slate-400">
                  <div>RGB: ({selectedRoll1.avg_rgb?.join(', ') || '—'})</div>
                  <div>L*: {selectedRoll1.avg_l?.toFixed(2)} | a*: {selectedRoll1.avg_a?.toFixed(2)} | b*: {selectedRoll1.avg_b?.toFixed(2)}</div>
                </div>
              </div>

              {/* Delta E Result */}
              <div className="glass-card p-6 flex flex-col items-center justify-center" style={{ cursor: 'default' }}>
                <div className="text-sm text-slate-500 uppercase tracking-wider mb-2">Delta E</div>
                {results ? (
                  <>
                    <div className="text-4xl font-bold text-white mb-2">
                      {results.delta_e_00.toFixed(4)}
                    </div>
                    <div className="text-xs text-slate-500 mb-4">CIEDE2000</div>
                    <div className="text-sm text-slate-400">
                      CIE76: {results.delta_e_76.toFixed(4)}
                    </div>
                    <div className="mt-4">
                      {results.delta_e_00 <= 0.6 ? (
                        <span className="badge badge-accepted">Match</span>
                      ) : results.delta_e_00 <= 0.8 ? (
                        <span className="badge badge-warning">Slight Variation</span>
                      ) : (
                        <span className="badge badge-rejected">Mismatch</span>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-slate-500 text-sm">
                    Run comparison on batch first
                  </div>
                )}
              </div>

              {/* Roll 2 */}
              <div className="glass-card p-6 text-center" style={{ cursor: 'default' }}>
                <h3 className="text-lg font-bold text-white mb-4">{selectedRoll2.roll_number}</h3>
                <div className="flex justify-center mb-4">
                  <ColorSwatch rgb={selectedRoll2.avg_rgb} size={120} />
                </div>
                <div className="space-y-1 text-sm text-slate-400">
                  <div>RGB: ({selectedRoll2.avg_rgb?.join(', ') || '—'})</div>
                  <div>L*: {selectedRoll2.avg_l?.toFixed(2)} | a*: {selectedRoll2.avg_a?.toFixed(2)} | b*: {selectedRoll2.avg_b?.toFixed(2)}</div>
                </div>
              </div>
            </div>

            {/* Pairwise Comparison Matrix */}
            {allResults.length > 0 && (
              <div className="glass-card p-6 overflow-x-auto" style={{ cursor: 'default' }}>
                <h3 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">
                  All Pairwise Comparisons
                </h3>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-2 px-3 text-slate-500">Roll 1</th>
                      <th className="text-left py-2 px-3 text-slate-500">Roll 2</th>
                      <th className="text-left py-2 px-3 text-slate-500">ΔE (CIE76)</th>
                      <th className="text-left py-2 px-3 text-slate-500">ΔE (CIEDE2000)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allResults.map(r => (
                      <tr key={r.id} className="border-b border-slate-800">
                        <td className="py-2 px-3 text-slate-300">{r.roll_1_number}</td>
                        <td className="py-2 px-3 text-slate-300">{r.roll_2_number}</td>
                        <td className="py-2 px-3 text-slate-400 font-mono">{r.delta_e_76.toFixed(4)}</td>
                        <td className="py-2 px-3 font-mono">
                          <span className={
                            r.delta_e_00 <= 0.6 ? 'text-green-400' :
                            r.delta_e_00 <= 0.8 ? 'text-amber-400' : 'text-red-400'
                          }>
                            {r.delta_e_00.toFixed(4)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </>
  );
}
