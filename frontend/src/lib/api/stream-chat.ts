import { getApiBaseUrl } from "@/lib/api";
import { tryGetSupabaseBrowserClient } from "@/lib/supabaseClient";
import type { ChatMessage } from "@/lib/api/chat";

export type StreamChatHandlers = {
  onToken: (text: string) => void;
  onDone: (sessionId: string) => void;
  onError: (message: string) => void;
};

function parseSseBlocks(buffer: string): { events: unknown[]; rest: string } {
  const events: unknown[] = [];
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  for (const block of parts) {
    for (const line of block.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const json = trimmed.slice(5).trim();
      try {
        events.push(JSON.parse(json));
      } catch {
        events.push(null);
      }
    }
  }
  return { events, rest };
}

async function resolveAccessToken(
  explicit: string | null | undefined,
): Promise<string | null> {
  if (explicit) return explicit;
  if (typeof window === "undefined") return null;
  const supabase = tryGetSupabaseBrowserClient();
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export async function streamChatRequest(
  messages: ChatMessage[],
  sessionId: string | null,
  accessToken: string | null,
  handlers: StreamChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const base = getApiBaseUrl();
  const token = await resolveAccessToken(accessToken);
  const res = await fetch(`${base}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      messages,
      session_id: sessionId,
      stream: true,
      structured_output: false,
    }),
    signal,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    handlers.onError(detail);
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    handlers.onError("No response body");
    return;
  }

  const decoder = new TextDecoder();
  let buf = "";

  function dispatch(ev: unknown) {
    if (!ev || typeof ev !== "object") return;
    const o = ev as { type?: string; text?: string; session_id?: string };
    if (o.type === "token" && typeof o.text === "string") {
      handlers.onToken(o.text);
    }
    if (o.type === "done" && typeof o.session_id === "string") {
      handlers.onDone(o.session_id);
    }
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const { events, rest } = parseSseBlocks(buf);
      buf = rest;
      for (const ev of events) dispatch(ev);
    }
    for (const line of buf.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      try {
        dispatch(JSON.parse(trimmed.slice(5).trim()));
      } catch {
        /* incomplete */
      }
    }
  } catch (e) {
    if (signal?.aborted) return;
    handlers.onError(e instanceof Error ? e.message : "Stream failed");
  }
}
