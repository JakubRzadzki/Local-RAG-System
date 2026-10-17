import { useRef, useState } from "react";
import type { DragEvent } from "react";
import type { UploadSettings } from "../types";

interface Props {
  uploading: string[];
  settings: UploadSettings;
  onSettings: (settings: UploadSettings) => void;
  onUpload: (files: File[]) => void;
}

const ACCEPT = ".txt,.md,.markdown,.pdf";

export function UploadZone({ uploading, settings, onSettings, onUpload }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    setDragging(false);
    onUpload(Array.from(event.dataTransfer.files));
  };

  return (
    <div className="upload">
      <div
        className={`dropzone${dragging ? " dragging" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <button type="button" onClick={() => inputRef.current?.click()}>
          Upload documents
        </button>
        <small>TXT, MD or PDF — or drop files here</small>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          multiple
          hidden
          onChange={(e) => {
            onUpload(Array.from(e.target.files ?? []));
            e.target.value = "";
          }}
        />
      </div>
      {uploading.map((name) => (
        <div key={name} className="uploading">
          <span className="spinner" /> Indexing {name}…
        </div>
      ))}
      <details className="chunk-settings">
        <summary>Chunking</summary>
        <label>
          Chunk size <b>{settings.chunkSize}</b>
          <input
            type="range"
            min={200}
            max={2000}
            step={100}
            value={settings.chunkSize}
            onChange={(e) =>
              onSettings({
                chunkSize: Number(e.target.value),
                chunkOverlap: Math.min(settings.chunkOverlap, Number(e.target.value) - 50),
              })
            }
          />
        </label>
        <label>
          Overlap <b>{settings.chunkOverlap}</b>
          <input
            type="range"
            min={0}
            max={Math.min(400, settings.chunkSize - 50)}
            step={20}
            value={settings.chunkOverlap}
            onChange={(e) => onSettings({ ...settings, chunkOverlap: Number(e.target.value) })}
          />
        </label>
        <small>Applies to files uploaded next.</small>
      </details>
    </div>
  );
}
