import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

import { LogsController } from './logs.controller';
import { LogsService } from './logs.service';
import { InferenceLogEntity } from './inference-log.entity';
import { InferenceErrorEntity } from './inference-error.entity';


@Module({
    imports: [TypeOrmModule.forFeature([InferenceLogEntity, InferenceErrorEntity])],
    controllers: [LogsController],
    providers: [LogsService],
})

export class LogsModule {}
