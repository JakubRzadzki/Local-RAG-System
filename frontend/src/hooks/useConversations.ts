import { useCallback, useEffect, useState } from "react";
import { deleteConversation, getConversations, renameConversation } from "../api/client";
import type { Conversation } from "../types";

interface UseConversations {
  conversations: Conversation[];
  refresh: () => Promise<void>;
  rename: (id: number, title: string) => Promise<void>;
  remove: (id: number) => Promise<void>;
}

export function useConversations(): UseConversations {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const refresh = useCallback(async () => {
    try {
      setConversations(await getConversations());
    } catch {
      // The sidebar list is non-critical; chat errors surface elsewhere.
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const rename = useCallback(async (id: number, title: string) => {
    const updated = await renameConversation(id, title);
    setConversations((all) => all.map((c) => (c.id === id ? updated : c)));
  }, []);

  const remove = useCallback(async (id: number) => {
    await deleteConversation(id);
    setConversations((all) => all.filter((c) => c.id !== id));
  }, []);

  return { conversations, refresh, rename, remove };
}
