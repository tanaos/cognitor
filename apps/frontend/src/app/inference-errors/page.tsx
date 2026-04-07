import InferenceErrorsTable from '../components/InferenceErrorsTable';
import { getInferenceErrors } from '../../services';

export const metadata = {
    title: 'Inference Errors | Tanaos Cognitor',
    description: 'View and analyze all inference errors detected in your models.'
};

interface Props {
    searchParams: Promise<{ errorId?: string }>;
}

export default async function InferenceErrorsPage({ searchParams }: Props) {
    const params = await searchParams;
    const { data: logs, error } = await getInferenceErrors();

    return (
        <div>
            <h1 className="page-title">Inference Errors</h1>
            <p className="page-subtitle">
                {(logs ?? []).length} entries
            </p>

            {error && <div className="error-banner">{error}</div>}

            <InferenceErrorsTable
                errors={logs ?? []}
                initialErrorId={params.errorId ? parseInt(params.errorId, 10) : undefined}
            />
        </div>
    );
}
