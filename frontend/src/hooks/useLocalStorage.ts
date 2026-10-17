import { useEffect, useState } from "react";
import type { Dispatch, SetStateAction } from "react";

/** `useState` that persists its value as JSON in localStorage. */
export function useLocalStorage<T>(key: string, initial: T): [T, Dispatch<SetStateAction<T>>] {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = window.localStorage.getItem(key);
      return stored === null ? initial : (JSON.parse(stored) as T);
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Storage may be unavailable (private mode); persistence is best-effort.
    }
  }, [key, value]);

  return [value, setValue];
}
