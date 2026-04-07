import type {
    DailyInferenceAggregateLogEntry,
    InferenceLogRecord,
    InferenceErrorRecord,
} from '@cognitor/shared';


const API = 'http://localhost:3001';

type FetchResult<T> = { data: T; error: null } | { data: null; error: string };

async function fetchLogs<T>(endpoint: string): Promise<FetchResult<T>> {
    try {
        const res = await fetch(`${API}${endpoint}`, { cache: 'no-store' });
        if (res.ok) {
            return { data: await res.json(), error: null };
        }
        const body = await res.json();
        return { data: null, error: body.message?.join(', ') ?? 'Failed to load logs' };
    } catch {
        return { data: null, error: 'Could not connect to backend' };
    }
}

export async function getInferenceLogs(): Promise<FetchResult<InferenceLogRecord[]>> {
    return fetchLogs<InferenceLogRecord[]>('/logs/inference-logs');
}

export async function getInferenceErrors(): Promise<FetchResult<InferenceErrorRecord[]>> {
    return fetchLogs<InferenceErrorRecord[]>('/logs/inference-errors');
}

export async function getDailyInferenceAggregates(): Promise<FetchResult<DailyInferenceAggregateLogEntry[]>> {
    return fetchLogs<DailyInferenceAggregateLogEntry[]>('/logs/daily-inference-aggregates');
}


