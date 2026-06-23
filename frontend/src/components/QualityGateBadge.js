'use client';

export default function QualityGateBadge({ status }) {
  const config = {
    accepted: { label: 'Accepted', icon: '✓', class: 'badge-accepted' },
    warning: { label: 'Warning', icon: '⚠', class: 'badge-warning' },
    rejected: { label: 'Rejected', icon: '✕', class: 'badge-rejected' },
    pending: { label: 'Pending', icon: '○', class: 'badge-pending' },
    scanned: { label: 'Scanned', icon: '◉', class: 'badge-scanned' },
  };

  const cfg = config[status] || config.pending;

  return (
    <span className={`badge ${cfg.class}`}>
      <span>{cfg.icon}</span>
      {cfg.label}
    </span>
  );
}
