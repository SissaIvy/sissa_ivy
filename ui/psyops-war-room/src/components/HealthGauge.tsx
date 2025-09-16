import React from 'react';
import { fetchHealth } from '../api/client';
import { useQuery } from '@tanstack/react-query';

export const HealthGauge: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetchHealth();
      if (!res.ok) throw new Error(res.message);
      return res.data;
    },
    staleTime: 10_000
  });

  if (isLoading) return <div style={{ fontSize: 12 }}>Loading health…</div>;
  if (!data) return <div style={{ fontSize: 12 }}>No data</div>;

  const pct = data.overall;
  const stroke = pct > 85 ? 'var(--color-success)' : pct > 60 ? 'var(--color-warning)' : 'var(--color-critical)';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <svg width={80} height={80} viewBox="0 0 100 100" role="img" aria-label={`Overall health ${pct}%`}>
        <circle cx={50} cy={50} r={42} stroke="var(--color-border)" strokeWidth={8} fill="none" />
        <circle
          cx={50}
          cy={50}
          r={42}
          stroke={stroke}
          strokeWidth={8}
          fill="none"
          strokeDasharray={`${(pct / 100) * 2 * Math.PI * 42} ${2 * Math.PI * 42}`}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
        />
        <text x="50" y="54" textAnchor="middle" fontSize={18} fill="var(--color-text)">{pct}</text>
      </svg>
      <div style={{ fontSize: 12, lineHeight: 1.5 }}>
        <div><strong>Overall</strong>: {pct}%</div>
        <div>Online: {data.totals.online}</div>
        <div>Offline: {data.totals.offline}</div>
        <div>Degraded: {data.totals.degraded}</div>
        <div style={{ opacity: 0.7 }}>Updated: {new Date(data.lastUpdated).toLocaleTimeString()}</div>
      </div>
    </div>
  );
};
