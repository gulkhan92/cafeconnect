import { useMutation } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { ChatMessageResponse } from "../types";

export function useSendChatMessage() {
  return useMutation({
    mutationFn: async (payload: { message: string; session_id?: string }) =>
      (await api.post<ChatMessageResponse>("/chat/message", payload)).data,
  });
}
