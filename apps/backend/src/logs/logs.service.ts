import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

import { InferenceLogEntity } from './inference-log.entity';
import { InferenceErrorEntity } from './inference-error.entity';
import { TrainingLogEntity } from './training-log.entity';


@Injectable()
export class LogsService {

    constructor(
        @InjectRepository(InferenceLogEntity)
        private readonly inferenceLogRepo: Repository<InferenceLogEntity>,

        @InjectRepository(InferenceErrorEntity)
        private readonly inferenceErrorRepo: Repository<InferenceErrorEntity>,

        @InjectRepository(TrainingLogEntity)
        private readonly trainingLogRepo: Repository<TrainingLogEntity>,
    ) {}

    async getInferenceLogs(): Promise<InferenceLogEntity[]> {
        return this.inferenceLogRepo.find({ 
            relations: ['error'], 
            order: { timestamp: 'DESC' } 
        });
    }

    async getTrainingLogs(): Promise<TrainingLogEntity[]> {
        return this.trainingLogRepo.find({ order: { timestamp: 'DESC' } });
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