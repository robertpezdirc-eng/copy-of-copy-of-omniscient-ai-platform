import React, { useState, useRef } from "react";
import { useChatStream } from "../hooks/useChatStream";

export default function OmniChatDashboard() {
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState("");
  const stopRef = useRef(null);
  const { stream } = useChatStream({ transport: "auto" });

  const handleSend = () => {
    if (!prompt.trim()) return;
    // stop previous stream
    if (typeof stopRef.current === "function") {
      stopRef.current();
      stopRef.current = null;
    }
    setMessages([]);

    let finalBuf = "";
    stopRef.current = stream({
      prompt,
      provider: "openai",
      onChunk: (chunk) => {
        setMessages((prev) => [...prev, chunk]);
        finalBuf += chunk;
      },
      onFinal: (full) => {
        setMessages((prev) => [...prev, `\n[FINAL] ${full}`]);
      },
      onEnd: () => {
        // if SSE (no explicit final), synthesize final
        if (finalBuf && !finalBuf.includes("[FINAL]")) {
          setMessages((prev) => [...prev, `\n[FINAL] ${finalBuf}`]);
        }
      },
      onError: (err) => {
        setMessages((prev) => [...prev, `[ERROR] ${err?.message || err}`]);
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
      <h2>OmniBrain Chat Dashboard</h2>
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
}