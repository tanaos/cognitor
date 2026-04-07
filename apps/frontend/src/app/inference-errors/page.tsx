export const metadata = {
    title: 'Inference Errors | Tanaos Cognitor',
    description: 'View and analyze all inference errors detected in your models.'
};
import Badge from '../components/Badge';
import Table from '../components/Table';
import { getInferenceErrors } from '../../services';


export default async function InferenceErrorsPage() {
    const { data: logs, error } = await getInferenceErrors();

    return (
        <div>
            <h1 className="page-title">Inference Errors</h1>
            <p className="page-subtitle">
                {(logs ?? []).length} entries
            </p>

            {error && <div className="error-banner">{error}</div>}

            <div className="table-card">
                <Table
                    columns={['Timestamp', 'Model', 'Exception Type', 'Message']}
                    rows={(logs ?? []).map((log) => [
                        log.inference_log ? new Date(log.inference_log.timestamp).toLocaleString() : '—',
                        log.inference_log?.model_name ?? '—',
                        <Badge key="type" label={log.exception_type ?? 'unknown'} variant="danger" />,
                        log.error_message,
                    ])}
                />
            </div>
        </div>
    );
}
