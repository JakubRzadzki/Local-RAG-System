interface Props {
  temperature: number;
  topK: number;
  onTemperature: (value: number) => void;
  onTopK: (value: number) => void;
}

export function SettingsPanel({ temperature, topK, onTemperature, onTopK }: Props) {
  return (
    <div className="settings-panel" role="group" aria-label="Generation settings">
      <label>
        <span>
          Temperature <b>{temperature.toFixed(1)}</b>
        </span>
        <input
          type="range"
          min={0}
          max={2}
          step={0.1}
          value={temperature}
          onChange={(e) => onTemperature(Number(e.target.value))}
        />
        <small>Low = factual, high = creative.</small>
      </label>
      <label>
        <span>
          Top-K sources <b>{topK}</b>
        </span>
        <input
          type="range"
          min={1}
          max={12}
          step={1}
          value={topK}
          onChange={(e) => onTopK(Number(e.target.value))}
        />
        <small>How many chunks are retrieved per question.</small>
      </label>
    </div>
  );
}
