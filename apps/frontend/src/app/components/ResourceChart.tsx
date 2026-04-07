'use client';

import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

import styles from './ChartCard.module.css';


export default function ResourceChart({ data }: {
    data: { time: string; cpu: number; ram: number }[];
}) {
    return (
        <div className={styles.card}>
            <h3 className={styles.title}>CPU & RAM usage over time</h3>
            <ResponsiveContainer width='100%' height={220}>
                <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                    <CartesianGrid strokeDasharray='3 3' stroke='var(--border)' />
                    <XAxis dataKey='time' tick={{ fontSize: 11 }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} unit='%' domain={[0, 100]} />
                    <Tooltip
                        contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid var(--border)' }}
                        formatter={(v, name) => [typeof v === 'number' ? `${v.toFixed(1)}%` : v, typeof name === 'string' ? name.toUpperCase() : name]}
                    />
                    <Legend iconType='circle' iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                    <Line type='monotone' dataKey='cpu' stroke='var(--primary)' strokeWidth={2} dot={false} name='cpu' />
                    <Line type='monotone' dataKey='ram' stroke='#6366f1' strokeWidth={2} dot={false} name='ram' />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
