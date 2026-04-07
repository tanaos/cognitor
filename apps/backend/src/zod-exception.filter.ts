import { ArgumentsHost, Catch, ExceptionFilter, HttpStatus } from '@nestjs/common';
import { Response } from 'express';
import { ZodError } from 'zod';


@Catch(ZodError)
export class ZodExceptionFilter implements ExceptionFilter {
    catch(exception: ZodError, host: ArgumentsHost) {
        const response = host.switchToHttp().getResponse<Response>();
        response.status(HttpStatus.UNPROCESSABLE_ENTITY).json({
            error: 'Unprocessable Entity',
            message: exception.issues.map((e) => `${e.path.join('.')}: ${e.message}`),
        });
    }
}
