import { Injectable, HttpException } from "@nestjs/common";
import axios from "axios";
import * as FormData from "form-data";

@Injectable()
export class ChatpdfService {
  private worker = axios.create({
    baseURL: process.env.PY_WORKER_URL, // http://localhost:8000
    timeout: 20000,
  });

  // Upload PDF
  async uploadPDF(file: Express.Multer.File) {
    try {
      const form = new FormData();
      form.append("file", file.buffer, {
        filename: file.originalname,
        contentType: file.mimetype,
      });

      const res = await this.worker.post("/process-pdf", form, {
        headers: form.getHeaders(),
      });

      return res.data;
    } catch (err: any) {
      console.error("UPLOAD ERROR:", err.response?.data || err.message);
      throw new HttpException("Worker upload failed", 500);
    }
  }

  // Ask RAG
  async askQuestion(payload: any) {
    try {
      const res = await this.worker.post("/ask", payload);
      return res.data;
    } catch (err: any) {
      console.error("ASK ERROR:", err.response?.data || err.message);
      throw new HttpException("Worker RAG failed", 500);
    }
  }
}
