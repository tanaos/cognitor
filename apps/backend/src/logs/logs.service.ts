import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

import { InferenceLogEntity } from './inference-log.entity';
import { InferenceErrorEntity } from './inference-error.entity';


@Injectable()
export class LogsService {

    constructor(
        @InjectRepository(InferenceLogEntity)
        private readonly inferenceLogRepo: Repository<InferenceLogEntity>,

        @InjectRepository(InferenceErrorEntity)
        private readonly inferenceErrorRepo: Repository<InferenceErrorEntity>,
    ) {}

    async getInferenceLogs(): Promise<InferenceLogEntity[]> {
        return this.inferenceLogRepo.find({ 
            relations: ['error'], 
            order: { timestamp: 'DESC' } 
        });
    }

    async getInferenceErrors(): Promise<InferenceErrorEntity[]> {
        return this.inferenceErrorRepo.find({
            relations: ['inference_log'],
            select: {
                id: true,
                inference_log_id: true,
                error_message: true,
                exception_type: true,
                inference_log: {
                    id: true,
                    model_name: true,
                    timestamp: true,
                    duration: true,
                },
            },
            order: { inference_log: { timestamp: 'DESC' } },
        });
    }
}