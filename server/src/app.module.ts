import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ChatpdfModule } from './modules/chatpdf/chatpdf.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    ChatpdfModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
