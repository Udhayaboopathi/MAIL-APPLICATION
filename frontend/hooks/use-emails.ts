import { useQuery } from "@tanstack/react-query";

import { apiFetch, type MailItem } from "../lib/api";
import { useUiStore } from "../store/ui-store";

export function useEmails() {
  const selectedFolder = useUiStore((state) => state.selectedFolder);
  return useQuery({
    queryKey: ["emails", selectedFolder],
    queryFn: () =>
      apiFetch<MailItem[]>(
        `/api/v1/mail/emails?folder=${encodeURIComponent(selectedFolder)}`,
      ),
  });
}
