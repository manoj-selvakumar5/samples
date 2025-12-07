/**
 * Minimal AG-UI Frontend using @ag-ui/client
 *
 * This demonstrates the AG-UI protocol directly - showing how events
 * stream from the Strands backend to the frontend.
 */

import { useState, useRef } from "react";
import { HttpAgent } from "@ag-ui/client";
import { Message } from "@ag-ui/core";

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const agentRef = useRef<HttpAgent | null>(null);

  const sendMessage = async () => {
    if (!input.trim() || streaming) return;

    // Create agent instance
    const agent = new HttpAgent({
      url: "http://localhost:8000",
      initialMessages: messages,
    });
    agentRef.current = agent;

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
    };
    agent.addMessage(userMessage);
    setMessages([...agent.messages]);
    setInput("");
    setStreaming(true);

    try {
      // Run the agent with a subscriber to track message changes
      await agent.runAgent(
        { tools: [], context: [] },
        {
          onMessagesChanged: ({ messages: newMessages }) => {
            setMessages([...newMessages]);
          },
        }
      );
    } catch (error) {
      console.error("AG-UI error:", error);
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 600,
        margin: "0 auto",
        padding: 20,
        fontFamily: "system-ui",
      }}
    >
      <h1 style={{ marginBottom: 8 }}>Strands Agent + AG-UI</h1>
      <p style={{ color: "#666", marginBottom: 20 }}>
        Real-time streaming via AG-UI protocol
      </p>

      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
          minHeight: 300,
          marginBottom: 16,
          backgroundColor: "#fafafa",
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: "#999" }}>Send a message to start chatting...</p>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            style={{
              marginBottom: 12,
              padding: 8,
              borderRadius: 4,
              backgroundColor: m.role === "user" ? "#e3f2fd" : "#fff",
            }}
          >
            <strong style={{ color: m.role === "user" ? "#1976d2" : "#333" }}>
              {m.role === "user" ? "You" : "Agent"}:
            </strong>{" "}
            {m.content}
          </div>
        ))}
        {streaming && <span style={{ color: "#999" }}>Thinking...</span>}
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type a message..."
          style={{
            flex: 1,
            padding: 12,
            fontSize: 16,
            border: "1px solid #ddd",
            borderRadius: 4,
          }}
          disabled={streaming}
        />
        <button
          onClick={sendMessage}
          disabled={streaming || !input.trim()}
          style={{
            padding: "12px 24px",
            fontSize: 16,
            backgroundColor: streaming || !input.trim() ? "#ccc" : "#1976d2",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: streaming || !input.trim() ? "not-allowed" : "pointer",
          }}
        >
          {streaming ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
