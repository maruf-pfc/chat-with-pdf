import {
  Controller,
  Post,
  Body,
  UploadedFile,
  UseInterceptors,
} from "@nestjs/common";
import { FileInterceptor } from "@nestjs/platform-express";
import { ChatpdfService } from "./chatpdf.service";

@Controller("chatpdf")
export class ChatpdfController {
  constructor(private readonly service: ChatpdfService) {}

  @Post("upload")
  @UseInterceptors(FileInterceptor("file"))
  async upload(@UploadedFile() file: Express.Multer.File) {
    if (!file) throw new Error("No file uploaded");
    return this.service.uploadPDF(file);
  }

  @Post("ask")
  async ask(@Body() body: any) {
    return this.service.askQuestion(body);
  }
}
