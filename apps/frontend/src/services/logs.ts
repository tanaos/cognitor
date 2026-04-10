import type {
    InferenceLogRecord,
    InferenceErrorRecord,
    TrainingLogRecord,
} from '@cognitor/shared';


const API = process.env.BACKEND_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:3001';

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

export async function getTrainingLogs(): Promise<FetchResult<TrainingLogRecord[]>> {
    return fetchLogs<TrainingLogRecord[]>('/logs/training-logs');
}


