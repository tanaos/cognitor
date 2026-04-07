import { Entity, Column, PrimaryGeneratedColumn, OneToOne } from 'typeorm';
import { InferenceErrorEntity } from './inference-error.entity';

@Entity('inference_logs')
export class InferenceLogEntity {
    @PrimaryGeneratedColumn()
    id: number;

    @Column({ name: 'model_name' })
    model_name: string;

    @Column()
    timestamp: string;

    @Column({ name: 'input_tokens' })
    input_tokens: number;

    @Column({ name: 'output_tokens' })
    output_tokens: number;

    @Column({ name: 'cpu_percent', type: 'float' })
    cpu_percent: number;

    @Column({ name: 'ram_usage_percent', type: 'float' })
    ram_usage_percent: number;

    @Column({ name: 'gpu_usage_percent', type: 'float', nullable: true })
    gpu_usage_percent: number | null;

    @Column({ type: 'float' })
    duration: number;

    @Column({ name: 'pre_inference_duration', type: 'float' })
    pre_inference_duration: number;

    @Column({ name: 'tokens_per_second', type: 'float', nullable: true })
    tokens_per_second: number | null;

    @Column({ name: 'time_to_first_token', type: 'float', nullable: true })
    time_to_first_token: number | null;

    @Column({ name: 'cpu_delta', type: 'float' })
    cpu_delta: number;

    @Column({ name: 'ram_delta', type: 'float' })
    ram_delta: number;

    @Column({ name: 'gpu_memory_reserved_mb', type: 'float', nullable: true })
    gpu_memory_reserved_mb: number | null;

    @Column({ name: 'gpu_memory_allocated_mb', type: 'float', nullable: true })
    gpu_memory_allocated_mb: number | null;

    @Column({ name: 'gpu_utilization_percent', type: 'float', nullable: true })
    gpu_utilization_percent: number | null;

    @Column({ name: 'generation_params', type: 'text' })
    generation_params: string;

    @Column({ name: 'stop_reason', nullable: true })
    stop_reason: string | null;

    @Column({ nullable: true })
    quantization: string | null;

    @Column({ name: 'device_name', nullable: true })
    device_name: string | null;

    @Column({ nullable: true })
    framework: string | null;

    @Column({ name: 'request_id', nullable: true })
    request_id: string | null;

    @Column({ name: 'session_id', nullable: true })
    session_id: string | null;

    @Column({ type: 'text' })
    input: string;

    @Column({ type: 'text' })
    output: string;

    @Column({ type: 'text' })
    extra: string;

    @OneToOne(() => InferenceErrorEntity, (error) => error.inference_log, { nullable: true, eager: false })
    error: InferenceErrorEntity | null;
}
