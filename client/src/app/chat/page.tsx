"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Upload, Send } from "lucide-react";
import axios from "axios";

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState("sess-" + Date.now());
  const [uploading, setUploading] = useState(false);

  // Backend URL
  const API_BASE = process.env.NEXT_PUBLIC_SERVER_URL;

  // Upload PDF
  const handleFileUpload = async (e: any) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await axios.post(`${API_BASE}/chatpdf/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setMessages((prev) => [
        ...prev,
        { role: "system", content: `Uploaded: ${file.name}` },
      ]);
    } catch (err) {
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  // Ask Question
  const sendMessage = async () => {
    if (!question.trim()) return;

    const userMessage = question;
    setQuestion("");

    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/chatpdf/ask`, {
        session_id: sessionId,
        question: userMessage,
      });

      const prompt = res.data.prompt; // plain text from worker

      setMessages((prev) => [...prev, { role: "assistant", content: prompt }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "❌ Error reaching AI worker." },
      ]);
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0a] text-gray-200">
      {/* Top Bar */}
      <div className="border-b border-gray-800 p-4 flex justify-between items-center">
        <h1 className="text-lg font-semibold">📄 Chat with PDF</h1>

        <label className="cursor-pointer">
          <div className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg">
            <Upload size={18} />
            <span>{uploading ? "Uploading..." : "Upload PDF"}</span>
          </div>
          <input type="file" className="hidden" onChange={handleFileUpload} />
        </label>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`max-w-3xl p-4 rounded-xl text-sm whitespace-pre-wrap ${
              msg.role === "assistant"
                ? "bg-gray-800 border border-gray-700 ml-0"
                : msg.role === "system"
                ? "text-gray-400 text-center"
                : "bg-blue-600 text-white ml-auto"
            }`}
          >
            {msg.content}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-gray-400">
            <Loader2 className="animate-spin" />
            Thinking...
          </div>
        )}
      </div>

      {/* Bottom Input */}
      <div className="p-4 border-t border-gray-800 bg-[#0f0f0f]">
        <div className="flex gap-2">
          <Input
            className="bg-gray-900 border-gray-700 text-gray-200"
            placeholder="Ask something about the uploaded PDFs..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <Button
            onClick={sendMessage}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
}
