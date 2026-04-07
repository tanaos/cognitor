'use client';

import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

import styles from './ChartCard.module.css';


export default function ModelUsageChart({ data }: {
    data: { model: string; count: number }[];
}) {
    return (
        <div className={styles.card}>
            <h3 className={styles.title}>Model usage</h3>
            {data.length === 0 ? (
                <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', fontSize: 14 }}>
                    No data available
                </div>
            ) : (
            <ResponsiveContainer width='100%' height={220}>
                <BarChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                    <CartesianGrid strokeDasharray='3 3' stroke='var(--border)' vertical={false} />
                    <XAxis dataKey='model' tick={{ fontSize: 11 }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip
                        contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid var(--border)' }}
                        formatter={(v) => [v, 'Inferences']}
                    />
                    <Bar dataKey='count' fill='var(--primary)' radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
            )}
        </div>
    );
}
