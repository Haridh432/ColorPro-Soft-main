'use client';
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
);

export default function DeltaEChart({ rolls, warnThreshold = 0.6, rejectThreshold = 0.8 }) {
  if (!rolls || rolls.length === 0) return null;

  const scannedRolls = rolls.filter(r => r.delta_e != null);
  if (scannedRolls.length === 0) return null;

  const labels = scannedRolls.map(r => r.roll_number);
  const deltaEValues = scannedRolls.map(r => r.delta_e);

  const barColors = deltaEValues.map(de => {
    if (de <= warnThreshold) return 'rgba(34, 197, 94, 0.7)';
    if (de <= rejectThreshold) return 'rgba(245, 158, 11, 0.7)';
    return 'rgba(239, 68, 68, 0.7)';
  });

  const data = {
    labels,
    datasets: [
      {
        label: 'ΔE (CIEDE2000)',
        data: deltaEValues,
        backgroundColor: barColors,
        borderColor: barColors.map(c => c.replace('0.7', '1')),
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(59, 130, 246, 0.3)',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        padding: 12,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        ticks: { color: '#64748b', font: { size: 11 } },
        grid: { display: false },
      },
      y: {
        beginAtZero: true,
        ticks: { color: '#64748b', font: { size: 11 } },
        grid: { color: 'rgba(30, 41, 59, 0.5)' },
      },
    },
  };

  return (
    <div className="glass-card p-6" style={{ cursor: 'default' }}>
      <h3 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">
        Delta E Distribution
      </h3>
      <div style={{ height: '300px' }}>
        <Bar data={data} options={options} />
      </div>
      <div className="flex items-center gap-6 mt-4 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm" style={{ background: 'rgba(34,197,94,0.7)' }} />
          Accepted (≤{warnThreshold})
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm" style={{ background: 'rgba(245,158,11,0.7)' }} />
          Warning ({warnThreshold}-{rejectThreshold})
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm" style={{ background: 'rgba(239,68,68,0.7)' }} />
          Rejected (&gt;{rejectThreshold})
        </span>
      </div>
    </div>
  );
}
