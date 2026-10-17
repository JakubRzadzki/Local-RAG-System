import type { Source } from "../types";

interface Props {
  sources: Source[];
  onOpen: (documentId: number, chunkIndex: number) => void;
}

export function SourceList({ sources, onOpen }: Props) {
  if (sources.length === 0) {
    return null;
  }
  return (
    <details className="sources">
      <summary>
        {sources.length} source{sources.length === 1 ? "" : "s"}
      </summary>
      <ol>
        {sources.map((source) => (
          <li key={source.index} className="source-card">
            <header>
              <span className="source-index">[{source.index}]</span>
              <span className="source-file">{source.filename}</span>
              <span className="source-tags">
                <span>chunk {source.chunk_index}</span>
                {source.page !== null && <span>page {source.page}</span>}
                <span title="Cosine similarity">{(source.score * 100).toFixed(0)}% match</span>
              </span>
            </header>
            <p>{source.content}</p>
            <button
              type="button"
              className="link-button"
              onClick={() => onOpen(source.document_id, source.chunk_index)}
            >
              View in document
            </button>
          </li>
        ))}
      </ol>
    </details>
  );
}
