import { useState } from "react";
import type { Conversation, RagDocument, UploadSettings } from "../types";
import { ConversationList } from "./ConversationList";
import { DocumentList } from "./DocumentList";
import { UploadZone } from "./UploadZone";

type Tab = "chats" | "documents";

interface Props {
  conversations: Conversation[];
  activeConversationId: number | null;
  documents: RagDocument[];
  uploading: string[];
  scope: number[];
  uploadSettings: UploadSettings;
  error: string | null;
  onNewChat: () => void;
  onOpenConversation: (id: number) => void;
  onRenameConversation: (id: number, title: string) => void;
  onDeleteConversation: (id: number) => void;
  onToggleScope: (id: number) => void;
  onClearScope: () => void;
  onUpload: (files: File[]) => void;
  onUploadSettings: (settings: UploadSettings) => void;
  onDeleteDocument: (id: number) => void;
  onPreview: (id: number) => void;
  onDismissError: () => void;
}

export function Sidebar(props: Props) {
  const { documents, scope } = props;
  const [tab, setTab] = useState<Tab>("chats");

  return (
    <aside className="sidebar">
      <div className="brand">Local RAG</div>
      <button type="button" className="new-chat" onClick={props.onNewChat}>
        + New chat
      </button>

      <div className="tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "chats"}
          className={tab === "chats" ? "active" : undefined}
          onClick={() => setTab("chats")}
        >
          Chats
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "documents"}
          className={tab === "documents" ? "active" : undefined}
          onClick={() => setTab("documents")}
        >
          Documents ({documents.length})
        </button>
      </div>

      {tab === "chats" ? (
        <ConversationList
          conversations={props.conversations}
          activeId={props.activeConversationId}
          onOpen={props.onOpenConversation}
          onRename={props.onRenameConversation}
          onDelete={props.onDeleteConversation}
        />
      ) : (
        <>
          <p className="scope-hint">
            {scope.length === 0
              ? "Searching all documents"
              : `Searching ${scope.length} of ${documents.length} selected`}
            {scope.length > 0 && (
              <>
                {" · "}
                <button type="button" className="link-button" onClick={props.onClearScope}>
                  Use all
                </button>
              </>
            )}
          </p>
          <DocumentList
            documents={documents}
            scope={scope}
            onToggle={props.onToggleScope}
            onDelete={props.onDeleteDocument}
            onPreview={props.onPreview}
          />
          {props.error && (
            <div className="banner error" role="alert">
              <span>{props.error}</span>
              <button type="button" className="link-button" onClick={props.onDismissError}>
                Dismiss
              </button>
            </div>
          )}
          <UploadZone
            uploading={props.uploading}
            settings={props.uploadSettings}
            onSettings={props.onUploadSettings}
            onUpload={props.onUpload}
          />
        </>
      )}
    </aside>
  );
}
