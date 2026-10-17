import type { RagDocument } from "../types";
import { formatBytes } from "../utils/format";

interface Props {
  documents: RagDocument[];
  scope: number[];
  onToggle: (id: number) => void;
  onDelete: (id: number) => void;
}

export function DocumentList({ documents, scope, onToggle, onDelete }: Props) {
  if (documents.length === 0) {
    return <p className="muted empty-docs">No documents yet. Upload a file to start.</p>;
  }
  return (
    <ul className="doc-list">
      {documents.map((doc) => (
        <li key={doc.id}>
          <label title="Limit answers to the selected documents">
            <input
              type="checkbox"
              checked={scope.includes(doc.id)}
              onChange={() => onToggle(doc.id)}
            />
            <span className="doc-meta">
              <span className="doc-name">{doc.filename}</span>
              <small>
                {doc.chunk_count} chunks · {formatBytes(doc.size_bytes)}
              </small>
            </span>
          </label>
          <button
            type="button"
            className="icon-button"
            aria-label={`Delete ${doc.filename}`}
            onClick={() => onDelete(doc.id)}
          >
            ✕
          </button>
        </li>
      ))}
    </ul>
  );
}
