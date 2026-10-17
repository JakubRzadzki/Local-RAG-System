import { useCallback, useEffect, useState } from "react";
import { deleteDocument, getDocuments, uploadDocument } from "../api/client";
import type { RagDocument, UploadSettings } from "../types";

interface UseDocuments {
  documents: RagDocument[];
  uploading: string[];
  error: string | null;
  upload: (files: File[], settings: UploadSettings) => Promise<void>;
  remove: (id: number) => Promise<void>;
  dismissError: () => void;
}

const messageOf = (e: unknown): string => (e instanceof Error ? e.message : "Unexpected error");

export function useDocuments(): UseDocuments {
  const [documents, setDocuments] = useState<RagDocument[]>([]);
  const [uploading, setUploading] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await getDocuments());
    } catch (e) {
      setError(messageOf(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const upload = useCallback(async (files: File[], settings: UploadSettings) => {
    for (const file of files) {
      setUploading((names) => [...names, file.name]);
      try {
        const created = await uploadDocument(file, settings);
        setDocuments((docs) => [created, ...docs]);
      } catch (e) {
        setError(`${file.name}: ${messageOf(e)}`);
      } finally {
        setUploading((names) => names.filter((n) => n !== file.name));
      }
    }
  }, []);

  const remove = useCallback(async (id: number) => {
    try {
      await deleteDocument(id);
      setDocuments((docs) => docs.filter((d) => d.id !== id));
    } catch (e) {
      setError(messageOf(e));
    }
  }, []);

  return { documents, uploading, error, upload, remove, dismissError: () => setError(null) };
}
