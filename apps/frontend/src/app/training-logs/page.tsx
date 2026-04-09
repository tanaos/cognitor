import TrainingLogsTable from '../components/TrainingLogsTable';
import { getTrainingLogs } from '../../services';

export const metadata = {
    title: 'Training Logs | Tanaos Cognitor',
    description: 'Browse and filter all training logs for your models.'
};

export default async function TrainingLogsPage() {
    const { data: logs, error } = await getTrainingLogs();

    return (
        <div>
            <h1 className='page-title'>Training Logs</h1>
            <p className='page-subtitle'>
                {(logs ?? []).length} entries
            </p>

            {error && <div className='error-banner'>{error}</div>}

            <TrainingLogsTable logs={logs ?? []} />
        </div>
    );
}
