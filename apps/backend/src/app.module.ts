import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

import { AppController } from './app.controller';
import { AppService } from './app.service';
import { LogsModule } from './logs/logs.module';
import { InferenceLogEntity } from './logs/inference-log.entity';
import { InferenceErrorEntity } from './logs/inference-error.entity';
import { TrainingLogEntity } from './logs/training-log.entity';


@Module({
    imports: [
        TypeOrmModule.forRoot({
            type: 'postgres',
            host: process.env.DB_HOST ?? 'localhost',
            port: parseInt(process.env.DB_PORT ?? '5432', 10),
            username: process.env.DB_USER ?? 'cognitoruser',
            password: process.env.DB_PASSWORD ?? 'cognitorpassword',
            database: process.env.DB_NAME ?? 'cognitor',
            entities: [InferenceLogEntity, InferenceErrorEntity, TrainingLogEntity],
            synchronize: true,
        }),
        LogsModule,
    ],
    controllers: [AppController],
    providers: [AppService],
})

export class AppModule {}
