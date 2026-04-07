'use client';

import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

import styles from './ChartCard.module.css';


export default function DurationChart({ data }: {
    data: { time: string; duration: number; model: string }[];
}) {
    return (
        <div className={styles.card}>
            <h3 className={styles.title}>Inference duration over time</h3>
            <ResponsiveContainer width='100%' height={220}>
                <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                    <CartesianGrid strokeDasharray='3 3' stroke='var(--border)' />
                    <XAxis dataKey='time' tick={{ fontSize: 11 }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} unit='s' />
                    <Tooltip
                        contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid var(--border)' }}
                        formatter={(v) => [typeof v === 'number' ? `${v.toFixed(4)}s` : v, 'Duration']}
                    />
                    <Line type='monotone' dataKey='duration' stroke='var(--primary)' strokeWidth={2} dot={false} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
