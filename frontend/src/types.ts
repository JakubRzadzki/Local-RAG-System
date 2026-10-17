/** Types mirroring the backend Pydantic schemas. */

export interface OllamaModel {
  name: string;
  size_bytes: number;
  family: string;
  parameter_size: string;
  quantization: string;
  capabilities: string[];
  supports_chat: boolean;
}

export interface ModelsResponse {
  models: OllamaModel[];
  embedding_model: string;
  embedding_model_installed: boolean;
}

export interface RagDocument {
  id: number;
  filename: string;
  content_type: string;
  size_bytes: number;
  chunk_count: number;
  chunk_size: number;
  chunk_overlap: number;
  created_at: string;
}

export interface Source {
  index: number;
  kind: "document" | "web";
  document_id: number | null;
  /** Document filename, or the page title for web results. */
  filename: string;
  chunk_index: number | null;
  page: number | null;
  url: string | null;
  score: number | null;
  content: string;
}

export interface ChatOptions {
  temperature: number;
  top_k: number;
  document_ids: number[] | null;
  web_search: boolean;
}

export interface ChatRequestMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  model: string;
  messages: ChatRequestMessage[];
  options: ChatOptions;
  conversation_id: number | null;
}

export type ChatEvent =
  | { type: "conversation"; id: number; title: string }
  | { type: "sources"; sources: Source[] }
  | { type: "token"; content: string }
  | { type: "ping" }
  | { type: "done" }
  | { type: "error"; message: string };

export interface UploadSettings {
  chunkSize: number;
  chunkOverlap: number;
}

export type MessageStatus = "streaming" | "done" | "error";

export interface UiMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
  status: MessageStatus;
  error?: string;
}

export interface Conversation {
  id: number;
  title: string;
  model: string;
  created_at: string;
  updated_at: string;
}

export interface StoredMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: StoredMessage[];
}

export interface ChunkPreview {
  chunk_index: number;
  page: number | null;
  content: string;
}

export interface DocumentPreview {
  document: RagDocument;
  chunks: ChunkPreview[];
}
