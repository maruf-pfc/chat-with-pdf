import { Module } from '@nestjs/common';
import { ChatpdfController } from './chatpdf.controller';
import { ChatpdfService } from './chatpdf.service';

@Module({
  controllers: [ChatpdfController],
  providers: [ChatpdfService]
})
export class ChatpdfModule {}
