export const metadata = {
    title: 'Inference Logs | Tanaos Cognitor',
    description: 'Browse and filter all inference logs for your models.'
};
import InferenceLogsTable from '../components/InferenceLogsTable';
import { getInferenceLogs } from '../../services';


interface Props {
    searchParams: Promise<{ model?: string; date?: string }>;
}

export default async function InferenceLogsPage({ searchParams }: Props) {
    const params = await searchParams;
    const { data: logs, error } = await getInferenceLogs();

    return (
        <div>
            <h1 className='page-title'>Inference Logs</h1>
            <p className='page-subtitle'>
                {(logs ?? []).length} entries
            </p>

            {error && <div className='error-banner'>{error}</div>}

            <InferenceLogsTable logs={logs ?? []} initialModel={params.model} initialDate={params.date} />
        </div>
    );
}
