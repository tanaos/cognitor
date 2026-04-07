import { Suspense } from 'react';

import Spinner from './components/Spinner';
import StatCard from './components/StatCard';
import DurationChart from './components/DurationChart';
import ResourceChart from './components/ResourceChart';
import ModelUsageChart from './components/ModelUsageChart';
import ErrorRateChart from './components/ErrorRateChart';
import PeriodFilter from './components/PeriodFilter';
import {
    getInferenceLogs,
    getInferenceErrors,
} from '../services';

export const metadata = {
    title: 'Dashboard | Tanaos Cognitor',
    description: 'Overview of Cognitor metrics, charts, and recent activity.'
};


export default async function Home({ searchParams }: { searchParams: Promise<{ period?: string; from?: string; to?: string }> }) {
    const { period = 'all', from: fromParam, to: toParam } = await searchParams;

    const [inferenceResult, errorsResult] = await Promise.all([
        getInferenceLogs(),
        getInferenceErrors(),
    ]);

    const allInferenceLogs = inferenceResult.data ?? [];
    const allInferenceErrors = errorsResult.data ?? [];

    // Compute date bounds
    const now = new Date();
    let fromDate: Date | null = null;
    let toDate: Date | null = null;

    if (period === 'custom') {
        if (fromParam) fromDate = new Date(fromParam);
        if (toParam) {
            toDate = new Date(toParam);
            toDate.setHours(23, 59, 59, 999);
        }
    } else {
        if (period === '24h') fromDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        else if (period === '7d') fromDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        else if (period === '30d') fromDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    }

    const inferenceLogs = allInferenceLogs.filter((l: any) => {
        const t = new Date(l.timestamp);
        if (fromDate && t < fromDate) return false;
        if (toDate && t > toDate) return false;
        return true;
    });
    const inferenceErrors = allInferenceErrors.filter((e: any) => {
        const t = new Date(e.inference_log?.timestamp);
        if (fromDate && t < fromDate) return false;
        if (toDate && t > toDate) return false;
        return true;
    });

    // Aggregate stats computed from raw logs
    const errorRate = inferenceLogs.length > 0
        ? ((inferenceErrors.length / inferenceLogs.length) * 100).toFixed(1)
        : '0.0';

    const avgDuration = inferenceLogs.length > 0
        ? inferenceLogs.reduce((sum: number, l: any) => sum + (l.duration ?? 0), 0) / inferenceLogs.length
        : null;

    const avgCpu = inferenceLogs.length > 0
        ? inferenceLogs.reduce((sum: number, l: any) => sum + (l.cpu_percent ?? 0), 0) / inferenceLogs.length
        : null;

    const avgRam = inferenceLogs.length > 0
        ? inferenceLogs.reduce((sum: number, l: any) => sum + (l.ram_usage_percent ?? 0), 0) / inferenceLogs.length
        : null;

    // Chart data
    const durationData = inferenceLogs.map((l: any) => ({
        time: new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        duration: l.duration,
        model: l.model_name ?? 'unknown',
    }));

    const resourceData = inferenceLogs.map((l: any) => ({
        time: new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        cpu: l.cpu_percent,
        ram: l.ram_usage_percent,
    }));

    // Model usage: count inferences per model
    const modelCounts: Record<string, number> = {};
    for (const l of inferenceLogs as any[]) {
        const name = l.model_name ?? 'unknown';
        modelCounts[name] = (modelCounts[name] ?? 0) + 1;
    }
    const modelUsageData = Object.entries(modelCounts).map(([model, count]) => ({ model, count }));

    // Error rate per day derived from log timestamps
    const dayTotals: Record<string, number> = {};
    const dayErrors: Record<string, number> = {};
    for (const l of inferenceLogs as any[]) {
        const date = l.timestamp?.split('T')[0] ?? '';
        if (!date) continue;
        dayTotals[date] = (dayTotals[date] ?? 0) + 1;
    }
    for (const e of inferenceErrors as any[]) {
        const date = e.inference_log?.timestamp?.split('T')[0] ?? '';
        if (!date) continue;
        dayErrors[date] = (dayErrors[date] ?? 0) + 1;
    }
    const errorRateData = Object.keys(dayTotals).sort().map((date) => ({
        date,
        errorRate: ((dayErrors[date] ?? 0) / dayTotals[date]) * 100,
    }));

    return (
        <div>
            <div className='page-header'>
                <div>
                    <h1 className='page-title'>Dashboard</h1>
                    <p className='page-subtitle'>
                        Overview of model inference and training activity
                    </p>
                </div>
            </div>

            <Suspense fallback={<Spinner size={24} />}>
                <PeriodFilter current={period} currentFrom={fromParam} currentTo={toParam} />
            </Suspense>

            <div className='stat-row'>
                <StatCard label='Total Inferences' value={inferenceLogs.length} />
                <StatCard label='Inference Errors' value={inferenceErrors.length} />
                <StatCard label='Error Rate' value={`${errorRate}%`} />
                {avgDuration !== null && (
                    <StatCard label='Avg Inference Duration' value={`${avgDuration.toFixed(3)}s`} />
                )}
                {avgCpu !== null && (
                    <StatCard label='Avg CPU Usage' value={`${avgCpu.toFixed(1)}%`} />
                )}
                {avgRam !== null && (
                    <StatCard label='Avg RAM Usage' value={`${avgRam.toFixed(1)}%`} />
                )}
            </div>

            {durationData.length === 0 && resourceData.length === 0 && modelUsageData.length === 0 && errorRateData.length === 0 ? (
                <div style={{ textAlign: 'center', margin: '2rem 0', fontSize: '1.2rem', color: '#888' }}>
                    No data to display for this interval
                </div>
            ) : (
                <>
                    <div className='charts-grid'>
                        <DurationChart data={durationData} />
                        <ResourceChart data={resourceData} />
                    </div>
                    <div className='charts-grid'>
                        <ModelUsageChart data={modelUsageData} />
                        <ErrorRateChart data={errorRateData} />
                    </div>
                </>
            )}
        </div>
    );
}
