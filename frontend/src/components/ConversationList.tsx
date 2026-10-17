import { useState } from "react";
import type { KeyboardEvent } from "react";
import type { Conversation } from "../types";

interface Props {
  conversations: Conversation[];
  activeId: number | null;
  onOpen: (id: number) => void;
  onRename: (id: number, title: string) => void;
  onDelete: (id: number) => void;
}

export function ConversationList({ conversations, activeId, onOpen, onRename, onDelete }: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");

  if (conversations.length === 0) {
    return <p className="muted empty-docs">No saved chats yet. Ask a question to start one.</p>;
  }

  const commit = (id: number): void => {
    const title = draft.trim();
    if (title) {
      onRename(id, title);
    }
    setEditingId(null);
  };

  const handleKey = (event: KeyboardEvent<HTMLInputElement>, id: number): void => {
    if (event.key === "Enter") {
      commit(id);
    } else if (event.key === "Escape") {
      setEditingId(null);
    }
  };

  return (
    <ul className="doc-list">
      {conversations.map((c) => (
        <li key={c.id} className={c.id === activeId ? "active" : undefined}>
          {editingId === c.id ? (
            <input
              className="rename-input"
              autoFocus
              value={draft}
              maxLength={120}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={() => commit(c.id)}
              onKeyDown={(e) => handleKey(e, c.id)}
            />
          ) : (
            <button type="button" className="conv-title" onClick={() => onOpen(c.id)} title={c.title}>
              {c.title}
            </button>
          )}
          <button
            type="button"
            className="icon-button"
            aria-label={`Rename ${c.title}`}
            onClick={() => {
              setDraft(c.title);
              setEditingId(c.id);
            }}
          >
            ✎
          </button>
          <button
            type="button"
            className="icon-button"
            aria-label={`Delete ${c.title}`}
            onClick={() => {
              if (window.confirm(`Delete chat "${c.title}"?`)) {
                onDelete(c.id);
              }
            }}
          >
            ✕
          </button>
        </li>
      ))}
    </ul>
  );
}
