'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

import styles from './PeriodFilter.module.css';
import FilterBar from './FilterBar';

const PERIODS = [
    { value: 'all', label: 'All time' },
    { value: '30d', label: 'Last 30 days' },
    { value: '7d', label: 'Last 7 days' },
    { value: '24h', label: 'Last 24 hours' },
];

export default function PeriodFilter({
    current,
    currentFrom,
    currentTo,
}: {
    current: string;
    currentFrom?: string;
    currentTo?: string;
}) {
    const router = useRouter();
    const searchParams = useSearchParams();
    const isCustomActive = current === 'custom';
    const [showCustom, setShowCustom] = useState(isCustomActive);
    const [from, setFrom] = useState(currentFrom ?? '');
    const [to, setTo] = useState(currentTo ?? '');

    function handlePreset(value: string) {
        setShowCustom(false);
        const params = new URLSearchParams(searchParams.toString());
        params.delete('period');
        params.delete('from');
        params.delete('to');
        if (value !== 'all') params.set('period', value);
        const query = params.toString();
        router.push(query ? `/?${query}` : '/');
    }

    function handleCustomApply() {
        if (!from && !to) return;
        const params = new URLSearchParams(searchParams.toString());
        params.delete('period');
        params.set('period', 'custom');
        if (from) params.set('from', from); else params.delete('from');
        if (to) params.set('to', to); else params.delete('to');
        router.push(`/?${params.toString()}`);
    }

    return (
        <FilterBar justify="start">
            <div className={styles.inner}>
            <div className={styles.container}>
                {PERIODS.map(p => (
                    <button
                        key={p.value}
                        className={`${styles.btn}${current === p.value && !isCustomActive ? ` ${styles.active}` : ''}`}
                        onClick={() => handlePreset(p.value)}
                    >
                        {p.label}
                    </button>
                ))}
                <button
                    className={`${styles.btn}${isCustomActive || showCustom ? ` ${styles.active}` : ''}`}
                    onClick={() => setShowCustom(v => !v)}
                >
                    Custom
                </button>
            </div>
            {showCustom && (
                <div className={styles.customRow}>
                    <input
                        type="date"
                        className={styles.dateInput}
                        value={from}
                        max={to || undefined}
                        onChange={e => setFrom(e.target.value)}
                    />
                    <span className={styles.dateSep}>to</span>
                    <input
                        type="date"
                        className={styles.dateInput}
                        value={to}
                        min={from || undefined}
                        onChange={e => setTo(e.target.value)}
                    />
                    <button
                        className={`${styles.btn} ${styles.applyBtn}`}
                        onClick={handleCustomApply}
                        disabled={!from && !to}
                    >
                        Apply
                    </button>
                </div>
            )}
            </div>
        </FilterBar>
    );
}
