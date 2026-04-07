'use client';

import { useState, useEffect, useRef, Fragment } from 'react';
import Link from 'next/link';

import Badge from './Badge';
import StatCard from './StatCard';
import FilterBar from './FilterBar';
import styles from './InferenceLogsTable.module.css';
import tableStyles from './Table.module.css';
import type { InferenceLogRecord } from '@cognitor/shared';


export default function InferenceLogsTable({ logs, initialModel, initialDate, initialLogId }: {
    logs: InferenceLogRecord[];
    initialModel?: string;
    initialDate?: string;
    initialLogId?: number;
}) {
    const models = Array.from(new Set(logs.map((l) => l.model_name)));
    const [modelFilter, setModelFilter] = useState(initialModel ?? 'all');
    const [minDuration, setMinDuration] = useState('');
    const [dateFilter, setDateFilter] = useState(initialDate ?? '');
    const [expanded, setExpanded] = useState<number | null>(null);
    const [highlightedId, setHighlightedId] = useState<number | undefined>(initialLogId);
    const highlightedRowRef = useRef<HTMLTableRowElement | null>(null);

    const filtered = logs.filter((l) => {
        if (modelFilter !== 'all' && l.model_name !== modelFilter) return false;
        if (minDuration && l.duration < parseFloat(minDuration)) return false;
        if (dateFilter && !l.timestamp.startsWith(dateFilter)) return false;
        return true;
    });

    const durations = filtered.map((l) => l.duration).sort((a, b) => a - b);
    const p90 = durations[Math.floor(durations.length * 0.90)] ?? 0;
    const p95 = durations[Math.floor(durations.length * 0.95)] ?? 0;
    const p99 = durations[Math.floor(durations.length * 0.99)] ?? 0;
    const tokenDurationRatios = filtered
        .filter((l) => l.duration > 0)
        .map((l) => l.input_tokens / l.duration);
    const avgTokenDuration = tokenDurationRatios.length
        ? tokenDurationRatios.reduce((a, b) => a + b, 0) / tokenDurationRatios.length
        : 0;

    useEffect(() => {
        if (initialLogId == null) return;
        const idx = filtered.findIndex((l) => l.id === initialLogId);
        if (idx !== -1) setExpanded(idx);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        highlightedRowRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, [expanded]);

    useEffect(() => {
        if (highlightedId == null) return;
        const handler = () => setHighlightedId(undefined);
        document.addEventListener('click', handler);
        return () => document.removeEventListener('click', handler);
    }, [highlightedId]);

    return (
        <div>
            {/* Derived metrics */}
            <div className={styles.metricsRow}>
                <StatCard label='Filtered entries' value={filtered.length} />
                <StatCard label='P90 Latency' value={`${p90.toFixed(4)}s`} />
                <StatCard label='P95 Latency' value={`${p95.toFixed(4)}s`} />
                <StatCard label='P99 Latency' value={`${p99.toFixed(4)}s`} />
                <StatCard label='Avg Tokens/s' value={avgTokenDuration.toFixed(2)} />
            </div>

            {/* Filters */}
            <FilterBar>
                <select
                    value={modelFilter}
                    onChange={(e) => setModelFilter(e.target.value)}
                    className={styles.select}
                >
                    <option value='all'>All models</option>
                    {models.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>

                <input
                    type='number'
                    placeholder='Min duration (s)'
                    value={minDuration}
                    onChange={(e) => setMinDuration(e.target.value)}
                    className={styles.inputText}
                />

                <input
                    type='date'
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                    className={styles.inputDate}
                />

                {(modelFilter !== 'all' || minDuration || dateFilter) && (
                    <button
                        onClick={() => { setModelFilter('all'); setMinDuration(''); setDateFilter(''); }}
                        className={styles.clearBtn}
                    >
                        Clear filters
                    </button>
                )}
            </FilterBar>

            {/* Table */}
            <div className={styles.tableWrapper}>
                <table className={tableStyles.table}>
                    <thead>
                        <tr className={tableStyles.headRow}>
                            {['', 'Timestamp', 'Model', 'Duration (s)', 'CPU %', 'RAM %', 'CPU Δ', 'RAM Δ', 'Input Tokens', 'Output Tokens', 'Tokens/s'].map((col) => (
                                <th key={col} className={tableStyles.headCell}>
                                    {col}
                                </th>
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
                                    ref={log.id === highlightedId ? highlightedRowRef : null}
                                    onClick={() => setExpanded(expanded === i ? null : i)}
                                    className={`${styles.row} ${expanded === i ? styles.rowExpanded : ''} ${log.id === highlightedId ? styles.highlighted : ''}`}
                                >
                                    <td className={styles.expandToggle}>
                                        <div className={styles.expandToggleInner}>
                                            <i className={`bi ${expanded === i ? 'bi-chevron-down' : 'bi-chevron-right'}`} />
                                            {log.error && (
                                                <Link
                                                    href={`/inference-errors?errorId=${log.error.id}`}
                                                    onClick={(e) => e.stopPropagation()}
                                                    className={styles.errorIcon}
                                                    title='View error details'
                                                >
                                                    <i className='bi bi-exclamation-circle-fill' />
                                                </Link>
                                            )}
                                        </div>
                                    </td>
                                    <td className={styles.cellNoWrap}>{new Date(log.timestamp).toLocaleString()}</td>
                                    <td className={tableStyles.cell}>
                                        <Badge label={log.model_name} />
                                    </td>
                                    <td className={styles.cellNumeric}>
                                        <span className={log.duration >= p95 ? styles.highlight : undefined}>
                                            {log.duration.toFixed(4)}
                                        </span>
                                    </td>
                                    <td className={tableStyles.cell}>{log.cpu_percent?.toFixed(1)}%</td>
                                    <td className={tableStyles.cell}>{log.ram_usage_percent?.toFixed(1)}%</td>
                                    <td className={tableStyles.cell}>{log.cpu_delta?.toFixed(1)}%</td>
                                    <td className={tableStyles.cell}>{log.ram_delta?.toFixed(1)}%</td>
                                    <td className={tableStyles.cell}>{log.input_tokens}</td>
                                    <td className={tableStyles.cell}>{log.output_tokens}</td>
                                    <td className={tableStyles.cell}>{log.tokens_per_second?.toFixed(2) ?? '—'}</td>
                                </tr>
                                {expanded === i && (
                                    <tr className={styles.detailRow}>
                                        <td colSpan={11} className={styles.detailCell}>
                                            <div className={styles.detailGrid}>
                                                <div>
                                                    <div className={styles.detailLabel}>Input</div>
                                                    <pre className={styles.pre}>
                                                        {log.input}
                                                    </pre>
                                                </div>
                                                <div>
                                                    <div className={styles.detailLabel}>Output</div>
                                                    <pre className={styles.pre}>
                                                        {log.output}
                                                    </pre>
                                                </div>
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
