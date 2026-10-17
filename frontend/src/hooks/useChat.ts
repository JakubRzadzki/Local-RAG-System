import { useCallback, useRef, useState } from "react";
import { getConversation, streamChat } from "../api/client";
import type { ChatEvent, ChatOptions, UiMessage } from "../types";

interface UseChat {
  messages: UiMessage[];
  conversationId: number | null;
  isStreaming: boolean;
  send: (text: string, model: string, options: ChatOptions) => Promise<void>;
  stop: () => void;
  clear: () => void;
  load: (conversationId: number) => Promise<void>;
}

let counter = 0;
const nextId = (): string => `m${Date.now()}-${counter++}`;

/**
 * Chat state and streaming. `onSaved` fires after each exchange so the caller can
 * refresh the conversation list (a new chat appears, ordering changes).
 */
export function useChat(onSaved: () => void): UseChat {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const patch = useCallback((id: string, update: (m: UiMessage) => UiMessage) => {
    setMessages((all) => all.map((m) => (m.id === id ? update(m) : m)));
  }, []);

  const stop = useCallback(() => abortRef.current?.abort(), []);

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
      // Skip empty answers (stopped before the first token) and failed ones: the backend
      // rejects empty messages, which would break every later question in this chat.
      const history = [...messages, userMessage]
        .filter((m) => m.status !== "error" && m.content.trim() !== "")
        .map(({ role, content }) => ({ role, content }));

      setMessages((all) => [...all, userMessage, assistantMessage]);
      setIsStreaming(true);
      const controller = new AbortController();
      abortRef.current = controller;

      const onEvent = (event: ChatEvent): void => {
        switch (event.type) {
          case "conversation":
            setConversationId(event.id);
            break;
          case "sources":
            patch(assistantId, (m) => ({ ...m, sources: event.sources }));
            break;
          case "ping":
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
        await streamChat(
          { model, messages: history, options, conversation_id: conversationId },
          onEvent,
          controller.signal,
        );
        patch(assistantId, (m) => (m.status === "streaming" ? { ...m, status: "done" } : m));
      } catch (e) {
        const message = e instanceof Error ? e.message : "Unexpected error";
        patch(assistantId, (m) => ({ ...m, status: "error", error: message }));
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
        onSaved();
      }
    },
    [messages, conversationId, patch, onSaved],
  );

  const clear = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setConversationId(null);
  }, []);

  const load = useCallback(async (id: number) => {
    abortRef.current?.abort();
    const detail = await getConversation(id);
    setMessages(
      detail.messages.map((m) => ({
        id: `s${m.id}`,
        role: m.role,
        content: m.content,
        sources: m.sources,
        status: "done",
      })),
    );
    setConversationId(detail.id);
  }, []);

  return { messages, conversationId, isStreaming, send, stop, clear, load };
}
