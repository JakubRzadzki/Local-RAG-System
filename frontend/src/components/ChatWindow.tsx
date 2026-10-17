import { useEffect, useRef } from "react";
import type { UiMessage } from "../types";
import { MessageBubble } from "./MessageBubble";

interface Props {
  messages: UiMessage[];
  hasDocuments: boolean;
  onSuggestion: (text: string) => void;
  onOpenSource: (documentId: number, chunkIndex: number) => void;
}

const SUGGESTIONS = [
  "How does this application work?",
  "Ile dni urlopu przysługuje pracownikowi NovaTech?",
  "Which planet has the strongest winds?",
  "What is the difference between RAG and fine-tuning?",
];

export function ChatWindow({ messages, hasDocuments, onSuggestion, onOpenSource }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="empty-state">
        <h1>Chat with your documents</h1>
        <p className="muted">
          Everything runs locally: embeddings, vector search and the language model.
        </p>
        {hasDocuments ? (
          <div className="suggestions">
            {SUGGESTIONS.map((text) => (
              <button key={text} type="button" onClick={() => onSuggestion(text)}>
                {text}
              </button>
            ))}
          </div>
        ) : (
          <p className="muted">Upload a document in the sidebar to get started.</p>
        )}
      </div>
    );
  }

  return (
    <div className="messages">
      <div className="messages-inner">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} onOpenSource={onOpenSource} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
