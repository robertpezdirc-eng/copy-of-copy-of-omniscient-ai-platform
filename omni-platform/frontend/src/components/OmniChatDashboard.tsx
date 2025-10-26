import React, { useRef, useState } from "react";
import { useChatStream } from "../hooks/useChatStream";

type Props = {};

type StreamStopper = () => void;

const OmniChatDashboard: React.FC<Props> = () => {
  const [messages, setMessages] = useState<string[]>([]);
  const [prompt, setPrompt] = useState<string>("");
  const stopRef = useRef<StreamStopper | null>(null);
  const { stream } = useChatStream({ transport: "auto" });

  const handleSend = () => {
    if (!prompt.trim()) return;

    if (typeof stopRef.current === "function") {
      stopRef.current();
      stopRef.current = null;
    }
    setMessages([]);

    let finalBuf = "";
    stopRef.current = stream({
      prompt,
      provider: "openai",
      onChunk: (chunk: string) => {
        setMessages((prev) => [...prev, chunk]);
        finalBuf += chunk;
      },
      onFinal: (full: string) => {
        setMessages((prev) => [...prev, `\n[FINAL] ${full}`]);
      },
      onEnd: () => {
        if (finalBuf && !finalBuf.includes("[FINAL]")) {
          setMessages((prev) => [...prev, `\n[FINAL] ${finalBuf}`]);
        }
      },
      onError: (err: any) => {
        const msg = err?.message ?? String(err);
        setMessages((prev) => [...prev, `[ERROR] ${msg}`]);
      },
    });
  };

  const handleStop = () => {
    if (typeof stopRef.current === "function") {
      stopRef.current();
      stopRef.current = null;
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif" }}>
      <h2>OmniBrain Chat Dashboard (TS)</h2>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Vnesi vprašanje..."
        style={{ width: "100%", height: "60px" }}
      />
      <div style={{ marginTop: "10px", display: "flex", gap: "8px" }}>
        <button onClick={handleSend}>Pošlji</button>
        <button onClick={handleStop}>Ustavi</button>
      </div>
      <div
        style={{
          marginTop: "20px",
          padding: "10px",
          border: "1px solid #ccc",
          minHeight: "150px",
          whiteSpace: "pre-wrap",
        }}
      >
        {messages.length === 0
          ? "Odgovori se bodo prikazali tukaj..."
          : messages.join("\n")}
      </div>
    </div>
  );
};

export default OmniChatDashboard;