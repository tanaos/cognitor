import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { ZodExceptionFilter } from './zod-exception.filter';


async function bootstrap() {
    const app = await NestFactory.create(AppModule);
    app.useGlobalFilters(new ZodExceptionFilter());

    const config = new DocumentBuilder()
        .setTitle('Cognitor Backend API')
        .setDescription('The Cognitor API')
        .setVersion('1.0')
        .build();
    const documentFactory = () => SwaggerModule.createDocument(app, config);
    SwaggerModule.setup('api', app, documentFactory);
    
    app.enableCors();
    await app.listen(3001, '0.0.0.0');
    console.log('Backend running on http://localhost:3001');
}
bootstrap();
