'use client';

import { useState, Fragment } from 'react';

import Badge from './Badge';
import StatCard from './StatCard';
import FilterBar from './FilterBar';
import styles from './TrainingLogsTable.module.css';
import tableStyles from './Table.module.css';
import type { TrainingLogRecord } from '@cognitor/shared';


function fmt(v: number | null | undefined, decimals = 4): string {
    if (v == null) return '—';
    return v.toFixed(decimals);
}

export default function TrainingLogsTable({ logs }: { logs: TrainingLogRecord[] }) {
    const models = Array.from(new Set(logs.map((l) => l.model_name).filter(Boolean))) as string[];
    const runs = Array.from(new Set(logs.map((l) => l.training_run_id).filter(Boolean))) as string[];

    const [modelFilter, setModelFilter] = useState('all');
    const [runFilter, setRunFilter] = useState('all');
    const [modeFilter, setModeFilter] = useState('all');
    const [dateFilter, setDateFilter] = useState('');
    const [expanded, setExpanded] = useState<number | null>(null);

    const modes = Array.from(new Set(logs.map((l) => l.mode).filter(Boolean))) as string[];

    const filtered = logs.filter((l) => {
        if (modelFilter !== 'all' && l.model_name !== modelFilter) return false;
        if (runFilter !== 'all' && l.training_run_id !== runFilter) return false;
        if (modeFilter !== 'all' && l.mode !== modeFilter) return false;
        if (dateFilter && l.timestamp && !l.timestamp.startsWith(dateFilter)) return false;
        return true;
    });

    const trainLosses = filtered.map((l) => l.train_loss).filter((v): v is number => v != null);
    const avgTrainLoss = trainLosses.length
        ? trainLosses.reduce((a, b) => a + b, 0) / trainLosses.length
        : null;

    const valLosses = filtered.map((l) => l.val_loss).filter((v): v is number => v != null);
    const avgValLoss = valLosses.length
        ? valLosses.reduce((a, b) => a + b, 0) / valLosses.length
        : null;

    const hasFilters = modelFilter !== 'all' || runFilter !== 'all' || modeFilter !== 'all' || dateFilter;
    const clearFilters = () => {
        setModelFilter('all');
        setRunFilter('all');
        setModeFilter('all');
        setDateFilter('');
    };

    return (
        <div>
            <div className={styles.metricsRow}>
                <StatCard label='Filtered entries' value={filtered.length} />
                <StatCard label='Avg Train Loss' value={avgTrainLoss != null ? avgTrainLoss.toFixed(4) : '—'} />
                <StatCard label='Avg Val Loss' value={avgValLoss != null ? avgValLoss.toFixed(4) : '—'} />
            </div>

            <FilterBar>
                <select value={modelFilter} onChange={(e) => setModelFilter(e.target.value)} className={styles.select}>
                    <option value='all'>All models</option>
                    {models.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>

                <select value={runFilter} onChange={(e) => setRunFilter(e.target.value)} className={styles.select}>
                    <option value='all'>All runs</option>
                    {runs.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>

                <select value={modeFilter} onChange={(e) => setModeFilter(e.target.value)} className={styles.select}>
                    <option value='all'>All modes</option>
                    {modes.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>

                <input
                    type='date'
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                    className={styles.inputDate}
                />

                {hasFilters && (
                    <button onClick={clearFilters} className={styles.clearBtn}>
                        Clear filters
                    </button>
                )}
            </FilterBar>

            <div className={styles.tableWrapper}>
                <table className={tableStyles.table}>
                    <thead>
                        <tr className={tableStyles.headRow}>
                            {['', 'Timestamp', 'Model', 'Run ID', 'Epoch', 'Step', 'Mode', 'Train Loss', 'Val Loss', 'LR', 'Duration (s)'].map((col) => (
                                <th key={col} className={tableStyles.headCell}>{col}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.length === 0 && (
                            <tr>
                                <td colSpan={11} className={tableStyles.empty}>
                                    No entries match the current filters.
                                </td>
                            </tr>
                        )}
                        {filtered.map((log, i) => (
                            <Fragment key={i}>
                                <tr
                                    onClick={() => setExpanded(expanded === i ? null : i)}
                                    className={`${styles.row} ${expanded === i ? styles.rowExpanded : ''}`}
                                >
                                    <td className={styles.expandToggle}>
                                        <i className={`bi ${expanded === i ? 'bi-chevron-down' : 'bi-chevron-right'}`} />
                                    </td>
                                    <td className={tableStyles.cell}>{log.timestamp ?? '—'}</td>
                                    <td className={tableStyles.cell}>
                                        {log.model_name ? <Badge label={log.model_name} /> : '—'}
                                    </td>
                                    <td className={tableStyles.cell}>{log.training_run_id ?? '—'}</td>
                                    <td className={tableStyles.cell}>{log.epoch ?? '—'}</td>
                                    <td className={tableStyles.cell}>{log.step ?? '—'}</td>
                                    <td className={tableStyles.cell}>{log.mode ?? '—'}</td>
                                    <td className={tableStyles.cell}>{fmt(log.train_loss)}</td>
                                    <td className={tableStyles.cell}>{fmt(log.val_loss)}</td>
                                    <td className={tableStyles.cell}>{fmt(log.learning_rate, 6)}</td>
                                    <td className={tableStyles.cell}>{fmt(log.duration, 2)}</td>
                                </tr>
                                {expanded === i && (
                                    <tr className={styles.detailRow}>
                                        <td colSpan={11}>
                                            <div className={styles.detailContent}>
                                                {[
                                                    ['Gradient Norm', fmt(log.gradient_norm)],
                                                    ['Samples/s', fmt(log.samples_per_second, 2)],
                                                    ['CPU %', fmt(log.cpu_percent, 1)],
                                                    ['RAM %', fmt(log.ram_usage_percent, 1)],
                                                    ['CPU Δ', fmt(log.cpu_delta, 2)],
                                                    ['RAM Δ', fmt(log.ram_delta, 2)],
                                                    ['GPU %', fmt(log.gpu_usage_percent, 1)],
                                                    ['GPU Mem Reserved (MB)', fmt(log.gpu_memory_reserved_mb, 1)],
                                                    ['GPU Mem Allocated (MB)', fmt(log.gpu_memory_allocated_mb, 1)],
                                                    ['GPU Utilization %', fmt(log.gpu_utilization_percent, 1)],
                                                    ['Quantization', log.quantization ?? '—'],
                                                    ['Device', log.device_name ?? '—'],
                                                    ['Framework', log.framework ?? '—'],
                                                    ['Extra', log.extra ?? '—'],
                                                ].map(([label, value]) => (
                                                    <div key={label} className={styles.detailItem}>
                                                        <span className={styles.detailLabel}>{label}</span>
                                                        <span className={styles.detailValue}>{value}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </Fragment>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
