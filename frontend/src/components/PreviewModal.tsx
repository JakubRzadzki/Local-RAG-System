import { useEffect, useRef, useState } from "react";
import { getDocumentPreview } from "../api/client";
import type { DocumentPreview } from "../types";
import { formatBytes } from "../utils/format";

interface Props {
  documentId: number;
  highlightChunk: number | null;
  onClose: () => void;
}

export function PreviewModal({ documentId, highlightChunk, onClose }: Props) {
  const [preview, setPreview] = useState<DocumentPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const highlightRef = useRef<HTMLElement>(null);

  useEffect(() => {
    let cancelled = false;
    setPreview(null);
    setError(null);
    getDocumentPreview(documentId)
      .then((data) => {
        if (!cancelled) {
          setPreview(data);
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Could not load the preview");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [documentId]);

  useEffect(() => {
    const onKey = (event: globalThis.KeyboardEvent): void => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    highlightRef.current?.scrollIntoView({ block: "center" });
  }, [preview]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="Document preview"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <strong>{preview?.document.filename ?? "Loading…"}</strong>
            {preview && (
              <small className="muted">
                {" "}
                · {preview.chunks.length} chunks · {formatBytes(preview.document.size_bytes)} ·
                chunk size {preview.document.chunk_size}, overlap {preview.document.chunk_overlap}
              </small>
            )}
          </div>
          <button type="button" className="icon-button visible" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>
        <div className="modal-body">
          {error && <div className="banner error">{error}</div>}
          {!preview && !error && <p className="muted">Loading…</p>}
          {preview?.chunks.map((chunk) => {
            const highlighted = chunk.chunk_index === highlightChunk;
            return (
              <section
                key={chunk.chunk_index}
                ref={highlighted ? highlightRef : undefined}
                className={`chunk${highlighted ? " highlighted" : ""}`}
              >
                <div className="chunk-label">
                  chunk {chunk.chunk_index}
                  {chunk.page !== null && ` · page ${chunk.page}`}
                </div>
                <p>{chunk.content}</p>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );
}
