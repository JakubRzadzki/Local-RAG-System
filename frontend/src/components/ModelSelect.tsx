import type { OllamaModel } from "../types";
import { formatBytes } from "../utils/format";

interface Props {
  models: OllamaModel[];
  selected: string;
  loading: boolean;
  onSelect: (name: string) => void;
}

export function ModelSelect({ models, selected, loading, onSelect }: Props) {
  if (loading) {
    return <span className="muted">Loading models…</span>;
  }
  if (models.length === 0) {
    return <span className="muted">No chat models found (run `ollama pull`)</span>;
  }
  return (
    <label className="model-select">
      <span className="visually-hidden">Language model</span>
      <select value={selected} onChange={(e) => onSelect(e.target.value)}>
        {models.map((m) => (
          <option key={m.name} value={m.name}>
            {m.name} · {m.parameter_size} · {formatBytes(m.size_bytes)}
          </option>
        ))}
      </select>
    </label>
  );
}
