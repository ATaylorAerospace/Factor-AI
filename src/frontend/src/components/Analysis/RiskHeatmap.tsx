import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface RiskHeatmapProps {
  riskScores: Record<string, unknown>[];
}

const COLORS: Record<string, string> = {
  critical: '#dc3545',
  high: '#fd7e14',
  medium: '#ffc107',
  low: '#28a745',
};

export function RiskHeatmap({ riskScores }: RiskHeatmapProps) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0 };

  for (const item of riskScores) {
    const level = (item.risk_level as string) || 'low';
    if (level in counts) counts[level as keyof typeof counts]++;
  }

  const data = [
    { name: 'Critical', value: counts.critical, level: 'critical' },
    { name: 'High', value: counts.high, level: 'high' },
    { name: 'Medium', value: counts.medium, level: 'medium' },
    { name: 'Low', value: counts.low, level: 'low' },
  ];

  return (
    <div
      style={{
        background: 'white',
        borderRadius: 12,
        padding: 24,
        marginBottom: 20,
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}
    >
      <h2 style={{ color: '#1a1a2e', marginBottom: 16 }}>Risk Distribution</h2>

      <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        {data.map((d) => (
          <div
            key={d.level}
            style={{
              flex: 1,
              textAlign: 'center',
              padding: 12,
              borderRadius: 8,
              background: `${COLORS[d.level]}15`,
            }}
          >
            <div style={{ fontSize: '2em', fontWeight: 700, color: COLORS[d.level] }}>
              {d.value}
            </div>
            <div style={{ fontSize: '0.85em', color: '#6c757d' }}>{d.name}</div>
          </div>
        ))}
      </div>

      {riskScores.length > 0 && (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data}>
            <XAxis dataKey="name" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((entry) => (
                <Cell key={entry.level} fill={COLORS[entry.level]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
