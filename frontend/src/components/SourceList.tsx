import type { Source } from "../types";

interface Props {
  sources: Source[];
  onOpen: (documentId: number, chunkIndex: number) => void;
}

function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function SourceCard({ source, onOpen }: { source: Source; onOpen: Props["onOpen"] }) {
  const isWeb = source.kind === "web" && source.url !== null;
  return (
    <li className="source-card">
      <header>
        <span className="source-index">[{source.index}]</span>
        {isWeb && source.url !== null ? (
          <a className="source-file" href={source.url} target="_blank" rel="noopener noreferrer">
            {source.filename}
          </a>
        ) : (
          <span className="source-file">{source.filename}</span>
        )}
        <span className="source-tags">
          {isWeb && source.url !== null ? (
            <span>🌐 {hostname(source.url)}</span>
          ) : (
            <>
              {source.chunk_index !== null && <span>chunk {source.chunk_index}</span>}
              {source.page !== null && <span>page {source.page}</span>}
              {source.score !== null && (
                <span title="Cosine similarity">{(source.score * 100).toFixed(0)}% match</span>
              )}
            </>
          )}
        </span>
      </header>
      <p>{source.content}</p>
      {!isWeb && source.document_id !== null && source.chunk_index !== null && (
        <button
          type="button"
          className="link-button"
          onClick={() => {
            if (source.document_id !== null && source.chunk_index !== null) {
              onOpen(source.document_id, source.chunk_index);
            }
          }}
        >
          View in document
        </button>
      )}
    </li>
  );
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
          <SourceCard key={source.index} source={source} onOpen={onOpen} />
        ))}
      </ol>
    </details>
  );
}
