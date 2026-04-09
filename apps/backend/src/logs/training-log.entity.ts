import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity('training_logs')
export class TrainingLogEntity {
    @PrimaryGeneratedColumn()
    id: number;

    @Column({ name: 'model_name', nullable: true })
    model_name: string | null;

    @Column({ nullable: true })
    timestamp: string | null;

    @Column({ name: 'training_run_id', nullable: true })
    training_run_id: string | null;

    @Column({ nullable: true })
    epoch: number | null;

    @Column({ nullable: true })
    step: number | null;

    @Column({ nullable: true })
    mode: string | null;

    @Column({ name: 'train_loss', type: 'float', nullable: true })
    train_loss: number | null;

    @Column({ name: 'val_loss', type: 'float', nullable: true })
    val_loss: number | null;

    @Column({ name: 'learning_rate', type: 'float', nullable: true })
    learning_rate: number | null;

    @Column({ name: 'gradient_norm', type: 'float', nullable: true })
    gradient_norm: number | null;

    @Column({ name: 'samples_per_second', type: 'float', nullable: true })
    samples_per_second: number | null;

    @Column({ type: 'float', nullable: true })
    duration: number | null;

    @Column({ name: 'cpu_percent', type: 'float', nullable: true })
    cpu_percent: number | null;

    @Column({ name: 'ram_usage_percent', type: 'float', nullable: true })
    ram_usage_percent: number | null;

    @Column({ name: 'cpu_delta', type: 'float', nullable: true })
    cpu_delta: number | null;

    @Column({ name: 'ram_delta', type: 'float', nullable: true })
    ram_delta: number | null;

    @Column({ name: 'gpu_usage_percent', type: 'float', nullable: true })
    gpu_usage_percent: number | null;

    @Column({ name: 'gpu_memory_reserved_mb', type: 'float', nullable: true })
    gpu_memory_reserved_mb: number | null;

    @Column({ name: 'gpu_memory_allocated_mb', type: 'float', nullable: true })
    gpu_memory_allocated_mb: number | null;

    @Column({ name: 'gpu_utilization_percent', type: 'float', nullable: true })
    gpu_utilization_percent: number | null;

    @Column({ nullable: true })
    quantization: string | null;

    @Column({ name: 'device_name', nullable: true })
    device_name: string | null;

    @Column({ nullable: true })
    framework: string | null;

    @Column({ type: 'text', nullable: true })
    extra: string | null;
}
