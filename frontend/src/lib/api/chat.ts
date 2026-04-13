import { apiClient } from "@/lib/api";
import type { ChatHistoryResponse } from "@/types/analysis";

export type ChatMessage = { role: string; content: string };

export type ChatJsonResponse = {
  reply: string;
  session_id?: string | null;
  structured?: unknown;
};

export async function postChatJson(
  messages: ChatMessage[],
  sessionId?: string | null,
): Promise<ChatJsonResponse> {
  const { data } = await apiClient.post<ChatJsonResponse>("/chat", {
    messages,
    session_id: sessionId ?? null,
    stream: false,
    structured_output: false,
  });
  return data;
}

export async function fetchChatHistory(
  sessionId: string,
): Promise<ChatHistoryResponse> {
  const { data } = await apiClient.get<ChatHistoryResponse>(
    `/chat-history/${sessionId}`,
  );
  return data;
}

export async function downloadAnalysisPdf(
  analysisId: string,
): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(
    `/download-report/${analysisId}`,
    { responseType: "blob" },
  );
  return data;
}
