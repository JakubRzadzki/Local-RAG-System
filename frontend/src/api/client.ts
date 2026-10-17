import type {
  ChatEvent,
  ChatRequest,
  Conversation,
  ConversationDetail,
  DocumentPreview,
  ModelsResponse,
  RagDocument,
  UploadSettings,
} from "../types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function readError(response: Response): Promise<ApiError> {
  let message = `Request failed (${response.status})`;
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body.detail)) {
      message = "Invalid request parameters.";
    }
  } catch {
    // Non-JSON error body; keep the generic message.
  }
  return new ApiError(message, response.status);
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new ApiError("Cannot reach the backend. Is it running on port 8000?", 0);
  }
  if (!response.ok) {
    throw await readError(response);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export const getModels = (): Promise<ModelsResponse> => request("/api/models");

export const getDocuments = (): Promise<RagDocument[]> => request("/api/documents");

export function uploadDocument(file: File, settings: UploadSettings): Promise<RagDocument> {
  const form = new FormData();
  form.append("file", file);
  form.append("chunk_size", String(settings.chunkSize));
  form.append("chunk_overlap", String(settings.chunkOverlap));
  return request("/api/documents", { method: "POST", body: form });
}

export const deleteDocument = (id: number): Promise<void> =>
  request(`/api/documents/${id}`, { method: "DELETE" });

export const getDocumentPreview = (id: number): Promise<DocumentPreview> =>
  request(`/api/documents/${id}/preview`);

export const getConversations = (): Promise<Conversation[]> => request("/api/conversations");

export const getConversation = (id: number): Promise<ConversationDetail> =>
  request(`/api/conversations/${id}`);

export const renameConversation = (id: number, title: string): Promise<Conversation> =>
  request(`/api/conversations/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });

export const deleteConversation = (id: number): Promise<void> =>
  request(`/api/conversations/${id}`, { method: "DELETE" });

/** POST a chat request and invoke `onEvent` for every NDJSON event as it arrives. */
export async function streamChat(
  payload: ChatRequest,
  onEvent: (event: ChatEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch {
    if (signal.aborted) {
      return;
    }
    throw new ApiError("Cannot reach the backend. Is it running on port 8000?", 0);
  }
  if (!response.ok || !response.body) {
    throw await readError(response);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const flushLines = (final: boolean): void => {
    const lines = buffer.split("\n");
    buffer = final ? "" : (lines.pop() ?? "");
    for (const line of lines) {
      if (line.trim()) {
        onEvent(JSON.parse(line) as ChatEvent);
      }
    }
  };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      flushLines(false);
    }
    buffer += decoder.decode();
    flushLines(true);
  } catch {
    if (!signal.aborted) {
      throw new ApiError(
        "The connection to the backend was interrupted. The answer above may be incomplete; " +
          "check that the backend is running and try again.",
        0,
      );
    }
  }
}
