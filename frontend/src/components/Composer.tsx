import { useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";

interface Props {
  disabled: boolean;
  isStreaming: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
  webSearch: boolean;
  onWebSearch: (enabled: boolean) => void;
}

export function Composer({
  disabled,
  isStreaming,
  onSend,
  onStop,
  webSearch,
  onWebSearch,
}: Props) {
  const [text, setText] = useState("");

  const submit = (event?: FormEvent): void => {
    event?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled || isStreaming) {
      return;
    }
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (event.key === "Enter" && !event.shiftKey) {
      submit(event);
    }
  };

  return (
    <form className="composer" onSubmit={submit}>
      <button
        type="button"
        className={`web-toggle${webSearch ? " on" : ""}`}
        aria-pressed={webSearch}
        title="Also search the web (the question is sent to DuckDuckGo)"
        onClick={() => onWebSearch(!webSearch)}
      >
        🌐 Web
      </button>
      <textarea
        value={text}
        rows={1}
        placeholder="Ask something about your documents…"
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      {isStreaming ? (
        <button type="button" className="send stop" onClick={onStop} aria-label="Stop generating">
          ■
        </button>
      ) : (
        <button type="submit" className="send" disabled={disabled || !text.trim()} aria-label="Send">
          ↑
        </button>
      )}
    </form>
  );
}
