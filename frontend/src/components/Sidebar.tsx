import type { RagDocument, UploadSettings } from "../types";
import { DocumentList } from "./DocumentList";
import { UploadZone } from "./UploadZone";

interface Props {
  documents: RagDocument[];
  uploading: string[];
  scope: number[];
  uploadSettings: UploadSettings;
  error: string | null;
  onNewChat: () => void;
  onToggleScope: (id: number) => void;
  onClearScope: () => void;
  onUpload: (files: File[]) => void;
  onUploadSettings: (settings: UploadSettings) => void;
  onDelete: (id: number) => void;
  onDismissError: () => void;
}

export function Sidebar(props: Props) {
  const { documents, scope } = props;
  return (
    <aside className="sidebar">
      <div className="brand">Local RAG</div>
      <button type="button" className="new-chat" onClick={props.onNewChat}>
        + New chat
      </button>

      <div className="sidebar-section-title">
        <span>Knowledge base</span>
        {scope.length > 0 && (
          <button type="button" className="link-button" onClick={props.onClearScope}>
            Use all
          </button>
        )}
      </div>
      <p className="scope-hint">
        {scope.length === 0
          ? "Searching all documents"
          : `Searching ${scope.length} of ${documents.length} selected`}
      </p>

      <DocumentList
        documents={documents}
        scope={scope}
        onToggle={props.onToggleScope}
        onDelete={props.onDelete}
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
    </aside>
  );
}
