import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

import { LogsController } from './logs.controller';
import { LogsService } from './logs.service';
import { InferenceLogEntity } from './inference-log.entity';
import { InferenceErrorEntity } from './inference-error.entity';
import { TrainingLogEntity } from './training-log.entity';


@Module({
    imports: [TypeOrmModule.forFeature([InferenceLogEntity, InferenceErrorEntity, TrainingLogEntity])],
    controllers: [LogsController],
    providers: [LogsService],
})

export class LogsModule {}
