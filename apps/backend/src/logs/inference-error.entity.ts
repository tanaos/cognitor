import { Entity, Column, PrimaryGeneratedColumn, OneToOne, JoinColumn } from 'typeorm';
import { InferenceLogEntity } from './inference-log.entity';

@Entity('inference_errors')
export class InferenceErrorEntity {
    @PrimaryGeneratedColumn()
    id: number;

    @Column({ name: 'inference_log_id' })
    inference_log_id: number;

    @Column({ name: 'error_message', type: 'text' })
    error_message: string;

    @Column({ name: 'exception_type', nullable: true })
    exception_type: string | null;

    @OneToOne(() => InferenceLogEntity, (log) => log.error)
    @JoinColumn({ name: 'inference_log_id' })
    inference_log: InferenceLogEntity;
}
