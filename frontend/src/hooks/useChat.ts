import { useCallback, useRef, useState } from "react";
import { streamChat } from "../api/client";
import type { ChatEvent, ChatOptions, UiMessage } from "../types";

interface UseChat {
  messages: UiMessage[];
  isStreaming: boolean;
  send: (text: string, model: string, options: ChatOptions) => Promise<void>;
  stop: () => void;
  clear: () => void;
}

let counter = 0;
const nextId = (): string => `m${Date.now()}-${counter++}`;

export function useChat(): UseChat {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const patch = useCallback((id: string, update: (m: UiMessage) => UiMessage) => {
    setMessages((all) => all.map((m) => (m.id === id ? update(m) : m)));
  }, []);

  const send = useCallback(
    async (text: string, model: string, options: ChatOptions) => {
      const userMessage: UiMessage = {
        id: nextId(),
        role: "user",
        content: text,
        sources: [],
        status: "done",
      };
      const assistantId = nextId();
      const assistantMessage: UiMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        sources: [],
        status: "streaming",
      };
      const history = [...messages, userMessage].map(({ role, content }) => ({ role, content }));

      setMessages((all) => [...all, userMessage, assistantMessage]);
      setIsStreaming(true);
      const controller = new AbortController();
      abortRef.current = controller;

      const onEvent = (event: ChatEvent): void => {
        switch (event.type) {
          case "sources":
            patch(assistantId, (m) => ({ ...m, sources: event.sources }));
            break;
          case "token":
            patch(assistantId, (m) => ({ ...m, content: m.content + event.content }));
            break;
          case "done":
            patch(assistantId, (m) => ({ ...m, status: "done" }));
            break;
          case "error":
            patch(assistantId, (m) => ({ ...m, status: "error", error: event.message }));
            break;
        }
      };

      try {
        await streamChat({ model, messages: history, options }, onEvent, controller.signal);
        patch(assistantId, (m) => (m.status === "streaming" ? { ...m, status: "done" } : m));
      } catch (e) {
        const message = e instanceof Error ? e.message : "Unexpected error";
        patch(assistantId, (m) => ({ ...m, status: "error", error: message }));
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [messages, patch],
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
  }, []);

  return { messages, isStreaming, send, stop, clear };
}
