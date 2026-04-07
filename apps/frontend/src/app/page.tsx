export const metadata = {
    title: 'Dashboard | Tanaos Cognitor',
    description: 'Overview of Cognitor metrics, charts, and recent activity.'
};
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
    getDailyInferenceAggregates,
} from '../services';


export default async function Home({ searchParams }: { searchParams: Promise<{ period?: string; from?: string; to?: string }> }) {
    const { period = 'all', from: fromParam, to: toParam } = await searchParams;

    const [inferenceResult, errorsResult, aggregatesResult] = await Promise.all([
        getInferenceLogs(),
        getInferenceErrors(),
        getDailyInferenceAggregates(),
    ]);

    const allInferenceLogs = inferenceResult.data ?? [];
    const allInferenceErrors = errorsResult.data ?? [];
    const allAggregates = aggregatesResult.data ?? [];

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

    const fromDateStr = fromDate ? fromDate.toISOString().split('T')[0] : null;
    const toDateStr = toDate ? toDate.toISOString().split('T')[0] : null;

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
    const aggregates = allAggregates.filter((a: any) => {
        if (fromDateStr && a.date < fromDateStr) return false;
        if (toDateStr && a.date > toDateStr) return false;
        return true;
    });
    const latestAggregate = aggregates[aggregates.length - 1];
    const errorRate = inferenceLogs.length > 0
        ? ((inferenceErrors.length / inferenceLogs.length) * 100).toFixed(1)
        : '0.0';

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

    const modelUsageData = latestAggregate?.model_usage_breakdown
        ? Object.entries(latestAggregate.model_usage_breakdown).map(([model, count]) => ({ model, count }))
        : [];

    const errorRateData = aggregates.map((a: any) => ({
        date: a.date,
        errorRate: a.total_inferences > 0
            ? (inferenceErrors.filter((e: any) => e.inference_log?.timestamp?.startsWith(a.date)).length / a.total_inferences) * 100
            : 0,
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

            {/* Stat cards */}
            <div className='stat-row'>
                <StatCard label='Total Inferences' value={inferenceLogs.length} />
                <StatCard label='Inference Errors' value={inferenceErrors.length} />
                <StatCard label='Error Rate' value={`${errorRate}%`} />
                {latestAggregate && (
                    <>
                        <StatCard
                            label='Avg Inference Duration'
                            value={`${latestAggregate.avg_inference_duration_seconds?.toFixed(3)}s`}
                            sub={`Latest: ${latestAggregate.date}`}
                        />
                        <StatCard
                            label='Avg CPU Usage'
                            value={`${latestAggregate.avg_cpu_usage_percent?.toFixed(1)}%`}
                            sub={`Latest: ${latestAggregate.date}`}
                        />
                        <StatCard
                            label='Avg RAM Usage'
                            value={`${latestAggregate.avg_ram_usage_percent?.toFixed(1)}%`}
                            sub={`Latest: ${latestAggregate.date}`}
                        />
                        {latestAggregate.avg_confidence_score != null && (
                            <StatCard
                                label='Avg Confidence'
                                value={latestAggregate.avg_confidence_score.toFixed(3)}
                                sub={`Latest: ${latestAggregate.date}`}
                            />
                        )}
                    </>
                )}
            </div>

            {/* Charts section */}
            {durationData.length === 0 && resourceData.length === 0 && modelUsageData.length === 0 && errorRateData.length === 0 ? (
                <div style={{ textAlign: 'center', margin: '2rem 0', fontSize: '1.2rem', color: '#888' }}>
                    No data to display for this interval
                </div>
            ) : (
                <>
                    {/* Charts row 1 */}
                    <div className='charts-grid'>
                        <DurationChart data={durationData} />
                        <ResourceChart data={resourceData} />
                    </div>

                    {/* Charts row 2 */}
                    <div className='charts-grid'>
                        <ModelUsageChart data={modelUsageData as any} />
                        <ErrorRateChart data={errorRateData} />
                    </div>

                </>
            )}
        </div>
    );
}

