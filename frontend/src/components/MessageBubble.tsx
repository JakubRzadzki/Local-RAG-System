import ReactMarkdown from "react-markdown";
import type { UiMessage } from "../types";
import { SourceList } from "./SourceList";

interface Props {
  message: UiMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div className={`message ${message.role}`}>
      <div className="avatar" aria-hidden="true">
        {isUser ? "You" : "AI"}
      </div>
      <div className="message-body">
        {isUser ? (
          <p className="user-text">{message.content}</p>
        ) : (
          <>
            <div className="markdown">
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {message.status === "streaming" && <span className="cursor" />}
            </div>
            {message.status === "error" && (
              <div className="banner error" role="alert">
                {message.error ?? "Something went wrong."}
              </div>
            )}
            <SourceList sources={message.sources} />
          </>
        )}
      </div>
    </div>
  );
}
