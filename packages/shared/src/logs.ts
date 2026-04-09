export interface InferenceErrorRecord {
    id: number;
    inference_log_id: number;
    error_message: string;
    exception_type: string | null;
    inference_log: {
        id: number;
        model_name: string;
        timestamp: string;
        duration: number;
    } | null;
}

export interface TrainingLogRecord {
    id: number;
    model_name: string | null;
    timestamp: string | null;
    training_run_id: string | null;
    epoch: number | null;
    step: number | null;
    mode: string | null;
    train_loss: number | null;
    val_loss: number | null;
    learning_rate: number | null;
    gradient_norm: number | null;
    samples_per_second: number | null;
    duration: number | null;
    cpu_percent: number | null;
    ram_usage_percent: number | null;
    cpu_delta: number | null;
    ram_delta: number | null;
    gpu_usage_percent: number | null;
    gpu_memory_reserved_mb: number | null;
    gpu_memory_allocated_mb: number | null;
    gpu_utilization_percent: number | null;
    quantization: string | null;
    device_name: string | null;
    framework: string | null;
    extra: string | null;
}

export interface InferenceLogRecord {
    id: number;
    model_name: string;
    timestamp: string;
    input_tokens: number;
    output_tokens: number;
    cpu_percent: number;
    ram_usage_percent: number;
    gpu_usage_percent: number | null;
    duration: number;
    pre_inference_duration: number;
    tokens_per_second: number | null;
    time_to_first_token: number | null;
    cpu_delta: number;
    ram_delta: number;
    gpu_memory_reserved_mb: number | null;
    gpu_memory_allocated_mb: number | null;
    gpu_utilization_percent: number | null;
    generation_params: string;
    stop_reason: string | null;
    quantization: string | null;
    device_name: string | null;
    framework: string | null;
    request_id: string | null;
    session_id: string | null;
    input: string;
    output: string;
    extra: string;
    error: InferenceErrorRecord | null;
}