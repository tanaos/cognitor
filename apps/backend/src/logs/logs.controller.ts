import { Controller, Get } from '@nestjs/common';
import { LogsService } from './logs.service';

@Controller('logs')
export class LogsController {
    constructor(private readonly logsService: LogsService) {}

    @Get('inference-logs')
    async getInferenceLogs() {
        return this.logsService.getInferenceLogs();
    }

    @Get('inference-errors')
    async getInferenceErrors() {
        return this.logsService.getInferenceErrors();
    }

    @Get('warnings')
    async getWarnings() {
        return [];
    }

    @Get('daily-inference-aggregates')
    async getDailyInferenceAggregates() {
        return [];
    }

    @Get('training-logs')
    async getTrainingLogs() {
        return [];
    }

    @Get('training-errors')
    async getTrainingErrors() {
        return [];
    }

    @Get('daily-training-aggregates')
    async getDailyTrainingAggregates() {
        return [];
    }
}