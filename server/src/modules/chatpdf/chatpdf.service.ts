import { Injectable, HttpException } from "@nestjs/common";
import axios from "axios";
import * as FormData from "form-data";

@Injectable()
export class ChatpdfService {
  private worker = axios.create({
    baseURL: process.env.PY_WORKER_URL, // e.g. http://localhost:8000
    timeout: 15000,
  });

  // ------------------
  // Upload PDF
  // ------------------
  async uploadPDF(file: Express.Multer.File) {
    try {
      const form = new FormData();
      form.append("file", file.buffer, {
        filename: file.originalname,
        contentType: file.mimetype,
      });

      const headers = form.getHeaders();

      const res = await this.worker.post("/process-pdf", form, {
        headers,
      });

      return res.data;
    } catch (err: any) {
      console.error("UPLOAD ERROR:", err.response?.data || err.message);
      throw new HttpException("Worker upload failed", 500);
    }
  }

  // ------------------
  // Ask RAG question
  // ------------------
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
