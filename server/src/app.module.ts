import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ChatpdfModule } from './modules/chatpdf/chatpdf.module';

@Module({
  imports: [ChatpdfModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
