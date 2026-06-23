'use client';
import Link from 'next/link';

export default function BatchCard({ batch, index = 0 }) {
  const total = batch.roll_count || 0;
  const scanned = batch.scanned_count || 0;
  const accepted = batch.accepted_count || 0;
  const warnings = batch.warning_count || 0;
  const rejected = batch.rejected_count || 0;
  const progress = total > 0 ? Math.round((scanned / total) * 100) : 0;

  return (
    <Link href={`/batch?id=${batch.id}`}>
      <div className={`glass-card p-6 cursor-pointer animate-fade-in stagger-${(index % 5) + 1}`}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-white">{batch.name}</h3>
            {batch.description && (
              <p className="text-sm text-slate-400 mt-1 line-clamp-1">{batch.description}</p>
            )}
          </div>
          <span className="text-xs text-slate-500">
            {new Date(batch.created_at).toLocaleDateString()}
          </span>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="text-center">
            <div className="text-xl font-bold text-white">{total}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Rolls</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-green-400">{accepted}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Accepted</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-amber-400">{warnings}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Warnings</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-red-400">{rejected}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Rejected</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="relative h-2 rounded-full overflow-hidden" style={{ background: 'rgba(30,41,59,0.8)' }}>
          <div
            className="absolute left-0 top-0 h-full rounded-full transition-all duration-500"
            style={{
              width: `${progress}%`,
              background: progress === 100
                ? 'linear-gradient(90deg, #22c55e, #16a34a)'
                : 'linear-gradient(90deg, #3b82f6, #2563eb)',
            }}
          />
        </div>
        <div className="flex justify-between mt-2">
          <span className="text-[10px] text-slate-500">{scanned}/{total} scanned</span>
          <span className="text-[10px] text-slate-500">{progress}%</span>
        </div>
      </div>
    </Link>
  );
}
