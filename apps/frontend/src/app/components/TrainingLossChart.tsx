'use client';

import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

import styles from './ChartCard.module.css';


export default function TrainingLossChart({ data }: {
    data: { time: string; train_loss: number | null; val_loss: number | null }[];
}) {
    return (
        <div className={styles.card}>
            <h3 className={styles.title}>Training &amp; validation loss over time</h3>
            {data.length === 0 ? (
                <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', fontSize: 14 }}>
                    No data available
                </div>
            ) : (
                <ResponsiveContainer width='100%' height={220}>
                    <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                        <CartesianGrid strokeDasharray='3 3' stroke='var(--border)' />
                        <XAxis dataKey='time' tick={{ fontSize: 11 }} tickLine={false} />
                        <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                        <Tooltip
                            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid var(--border)' }}
                            formatter={(value, name) => [typeof value === 'number' ? value.toFixed(4) : value, String(name ?? '')]}
                        />
                        <Legend wrapperStyle={{ fontSize: 12 }} />
                        <Line type='monotone' dataKey='train_loss' name='Train Loss' stroke='var(--primary)' strokeWidth={2} dot={false} connectNulls />
                        <Line type='monotone' dataKey='val_loss' name='Val Loss' stroke='#3b82f6' strokeWidth={2} dot={false} connectNulls />
                    </LineChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}
