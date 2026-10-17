import { useMemo, useState } from "react";
import { ChatWindow } from "./components/ChatWindow";
import { Composer } from "./components/Composer";
import { PreviewModal } from "./components/PreviewModal";
import { ModelSelect } from "./components/ModelSelect";
import { SettingsPanel } from "./components/SettingsPanel";
import { Sidebar } from "./components/Sidebar";
import { useChat } from "./hooks/useChat";
import { useConversations } from "./hooks/useConversations";
import { useDocuments } from "./hooks/useDocuments";
import { useLocalStorage } from "./hooks/useLocalStorage";
import { useModels } from "./hooks/useModels";
import type { UploadSettings } from "./types";

export default function App() {
  const models = useModels();
  const docs = useDocuments();
  const conversations = useConversations();
  const chat = useChat(conversations.refresh);

  const [temperature, setTemperature] = useLocalStorage("rag.temperature", 0.2);
  const [topK, setTopK] = useLocalStorage("rag.topK", 4);
  const [uploadSettings, setUploadSettings] = useLocalStorage<UploadSettings>("rag.upload", {
    chunkSize: 800,
    chunkOverlap: 100,
  });
  const [showSettings, setShowSettings] = useState(false);
  const [scope, setScope] = useState<number[]>([]);
  const [preview, setPreview] = useState<{ documentId: number; chunk: number | null } | null>(
    null,
  );
  const [chatError, setChatError] = useState<string | null>(null);

  // Ignore selections for documents that have since been deleted.
  const activeScope = useMemo(
    () => scope.filter((id) => docs.documents.some((d) => d.id === id)),
    [scope, docs.documents],
  );

  const toggleScope = (id: number): void =>
    setScope((ids) => (ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id]));

  const send = (text: string): void => {
    void chat.send(text, models.selected, {
      temperature,
      top_k: topK,
      document_ids: activeScope.length > 0 ? activeScope : null,
    });
  };

  const openConversation = (id: number): void => {
    setChatError(null);
    chat.load(id).catch((e: unknown) => {
      setChatError(e instanceof Error ? e.message : "Could not open the chat");
    });
  };

  const deleteConversation = (id: number): void => {
    conversations
      .remove(id)
      .then(() => {
        if (id === chat.conversationId) {
          chat.clear();
        }
      })
      .catch((e: unknown) => {
        setChatError(e instanceof Error ? e.message : "Could not delete the chat");
      });
  };

  const renameConversation = (id: number, title: string): void => {
    conversations.rename(id, title).catch((e: unknown) => {
      setChatError(e instanceof Error ? e.message : "Could not rename the chat");
    });
  };

  return (
    <div className="app">
      <Sidebar
        conversations={conversations.conversations}
        activeConversationId={chat.conversationId}
        onOpenConversation={openConversation}
        onRenameConversation={renameConversation}
        onDeleteConversation={deleteConversation}
        onPreview={(id) => setPreview({ documentId: id, chunk: null })}
        documents={docs.documents}
        uploading={docs.uploading}
        scope={activeScope}
        uploadSettings={uploadSettings}
        error={docs.error}
        onNewChat={() => {
          setChatError(null);
          chat.clear();
        }}
        onToggleScope={toggleScope}
        onClearScope={() => setScope([])}
        onUpload={(files) => void docs.upload(files, uploadSettings)}
        onUploadSettings={setUploadSettings}
        onDeleteDocument={(id) => void docs.remove(id)}
        onDismissError={docs.dismissError}
      />

      <main className="main">
        <header className="topbar">
          <ModelSelect
            models={models.chatModels}
            selected={models.selected}
            loading={models.loading}
            onSelect={models.select}
          />
          <button
            type="button"
            className="ghost"
            aria-expanded={showSettings}
            onClick={() => setShowSettings((open) => !open)}
          >
            ⚙ Parameters
          </button>
        </header>

        {showSettings && (
          <SettingsPanel
            temperature={temperature}
            topK={topK}
            onTemperature={setTemperature}
            onTopK={setTopK}
          />
        )}

        {models.error && (
          <div className="banner error" role="alert">
            {models.error}{" "}
            <button type="button" className="link-button" onClick={models.reload}>
              Retry
            </button>
          </div>
        )}
        {!models.error && !models.embeddingInstalled && (
          <div className="banner error" role="alert">
            Embedding model <code>{models.embeddingModel}</code> is not installed. Run{" "}
            <code>ollama pull {models.embeddingModel}</code>.
          </div>
        )}

        {chatError && (
          <div className="banner error" role="alert">
            {chatError}
          </div>
        )}

        <ChatWindow
          onOpenSource={(documentId, chunk) => setPreview({ documentId, chunk })}
          messages={chat.messages}
          hasDocuments={docs.documents.length > 0}
          onSuggestion={send}
        />

        <Composer
          disabled={!models.selected}
          isStreaming={chat.isStreaming}
          onSend={send}
          onStop={chat.stop}
        />
      </main>
      {preview && (
        <PreviewModal
          documentId={preview.documentId}
          highlightChunk={preview.chunk}
          onClose={() => setPreview(null)}
        />
      )}
    </div>
  );
}
