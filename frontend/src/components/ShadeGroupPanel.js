'use client';
import ColorSwatch from './ColorSwatch';
import QualityGateBadge from './QualityGateBadge';

export default function ShadeGroupPanel({ groups }) {
  if (!groups || Object.keys(groups).length === 0) {
    return (
      <div className="glass-card p-6 text-center" style={{ cursor: 'default' }}>
        <p className="text-slate-500">No shade groups available. Run clustering first.</p>
      </div>
    );
  }

  const groupColors = [
    'from-blue-500/10 to-blue-600/5',
    'from-purple-500/10 to-purple-600/5',
    'from-cyan-500/10 to-cyan-600/5',
    'from-emerald-500/10 to-emerald-600/5',
    'from-pink-500/10 to-pink-600/5',
    'from-amber-500/10 to-amber-600/5',
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        Shade Groups (ML Clustered)
      </h3>
      {Object.entries(groups).map(([groupNum, rolls], idx) => (
        <div
          key={groupNum}
          className={`glass-card p-5 bg-gradient-to-r ${groupColors[idx % groupColors.length]}`}
          style={{ cursor: 'default' }}
        >
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-bold text-white">
              Shade Group {groupNum}
            </h4>
            <span className="text-xs text-slate-400">{rolls.length} rolls</span>
          </div>
          <div className="flex flex-wrap gap-3">
            {rolls.map(roll => (
              <div
                key={roll.id}
                className="flex items-center gap-2 px-3 py-2 rounded-lg"
                style={{ background: 'rgba(0,0,0,0.2)' }}
              >
                <ColorSwatch rgb={roll.avg_rgb} size={28} />
                <div>
                  <div className="text-xs font-medium text-white">{roll.roll_number}</div>
                  <div className="text-[10px] text-slate-500">
                    ΔE: {roll.delta_e?.toFixed(3) || '—'}
                  </div>
                </div>
                <QualityGateBadge status={roll.status} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
