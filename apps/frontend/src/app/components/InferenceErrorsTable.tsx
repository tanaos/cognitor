'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { formatTimestamp } from '../../utils/formatTimestamp';

import Badge from './Badge';
import tableStyles from './Table.module.css';
import styles from './InferenceErrorsTable.module.css';
import type { InferenceErrorRecord } from '@cognitor/shared';


export default function InferenceErrorsTable({
    errors,
    initialErrorId,
}: {
    errors: InferenceErrorRecord[];
    initialErrorId?: number;
}) {
    const router = useRouter();
    const [highlightedId, setHighlightedId] = useState<number | undefined>(initialErrorId);
    const highlightedRowRef = useRef<HTMLTableRowElement | null>(null);

    useEffect(() => {
        highlightedRowRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, []);

    useEffect(() => {
        if (highlightedId == null) return;
        const handler = () => setHighlightedId(undefined);
        document.addEventListener('click', handler);
        return () => document.removeEventListener('click', handler);
    }, [highlightedId]);

    return (
        <div className={styles.tableWrapper}>
            <table className={tableStyles.table}>
                <thead>
                    <tr className={tableStyles.headRow}>
                        {['Timestamp', 'Model', 'Exception Type', 'Message'].map((col) => (
                            <th key={col} className={tableStyles.headCell}>{col}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {errors.map((err) => {
                        const isHighlighted = err.id === highlightedId;
                        return (
                            <tr
                                key={err.id}
                                ref={isHighlighted ? highlightedRowRef : null}
                                className={`${tableStyles.row} ${styles.clickableRow} ${isHighlighted ? styles.highlighted : ''}`}
                                onClick={() => {
                                    if (err.inference_log_id) {
                                        router.push(`/inference-logs?logId=${err.inference_log_id}`);
                                    }
                                }}
                            >
                                <td className={tableStyles.cell}>
                                    {err.inference_log
                                        ? formatTimestamp(err.inference_log.timestamp)
                                        : '—'}
                                </td>
                                <td className={tableStyles.cell}>
                                    {err.inference_log?.model_name ?? '—'}
                                </td>
                                <td className={tableStyles.cell}>
                                    <Badge label={err.exception_type ?? 'unknown'} variant='danger' />
                                </td>
                                <td className={tableStyles.cell}>{err.error_message}</td>
                            </tr>
                        );
                    })}
                    {errors.length === 0 && (
                        <tr>
                            <td colSpan={4} className={tableStyles.empty}>No entries found.</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
