"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import type { ChatMessage } from "@/lib/api/chat";
import { fetchChatHistory } from "@/lib/api/chat";
import { streamChatRequest } from "@/lib/api/stream-chat";
import { queryKeys } from "@/lib/query-keys";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";

const STORAGE_KEY = "mycareer_chat_session_id";

type Row = { role: string; content: string };

export function CareerChatPanel() {
  const queryClient = useQueryClient();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [messages, setMessages] = useState<Row[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    try {
      const sid = sessionStorage.getItem(STORAGE_KEY);
      if (sid) setSessionId(sid);
    } catch {
      /* ignore */
    }
    setHydrated(true);
  }, []);

  const historyQuery = useQuery({
    queryKey: queryKeys.chatHistory(sessionId ?? ""),
    queryFn: () => fetchChatHistory(sessionId!),
    enabled: hydrated && !!sessionId,
  });

  const historyBlocking = Boolean(sessionId && historyQuery.isLoading);

  useEffect(() => {
    if (!historyQuery.data?.messages?.length) return;
    setMessages(
      historyQuery.data.messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
    );
  }, [historyQuery.data]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || busy || historyBlocking) return;
    setErr(null);
    setInput("");
    const userRow: Row = { role: "user", content: text };
    const nextMessages = [...messages, userRow];
    setMessages(nextMessages);
    setBusy(true);
    setStreaming("");

    const payload: ChatMessage[] = nextMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const { data } = await getSupabaseBrowserClient().auth.getSession();
    const token = data.session?.access_token ?? null;

    abortRef.current?.abort();
    abortRef.current = new AbortController();

    let acc = "";
    try {
      await streamChatRequest(
        payload,
        sessionId,
        token,
        {
          onToken: (t) => {
            acc += t;
            setStreaming(acc);
          },
          onDone: (sid) => {
            setSessionId(sid);
            try {
              sessionStorage.setItem(STORAGE_KEY, sid);
            } catch {
              /* ignore */
            }
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: acc },
            ]);
            setStreaming("");
            void queryClient.invalidateQueries({
              queryKey: queryKeys.chatHistory(sid),
            });
          },
          onError: (msg) => {
            setErr(msg);
            setStreaming("");
          },
        },
        abortRef.current.signal,
      );
    } finally {
      setBusy(false);
    }
  }, [busy, historyBlocking, input, messages, sessionId, queryClient]);

  function newChat() {
    abortRef.current?.abort();
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
    setSessionId(null);
    setMessages([]);
    setStreaming("");
    setErr(null);
  }

  return (
    <Card className="mx-auto flex h-[min(720px,calc(100vh-8rem))] max-w-3xl flex-col">
      <CardHeader className="shrink-0 border-b pb-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle>Career mentor</CardTitle>
            <CardDescription>
              Streaming answers grounded on your resume and past analyses.
            </CardDescription>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={newChat}>
            New chat
          </Button>
        </div>
        {sessionId ? (
          <p className="mt-2 font-mono text-xs text-muted-foreground">
            Session: {sessionId.slice(0, 8)}…
          </p>
        ) : null}
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col gap-3 p-4 pt-4">
        {err ? (
          <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{err}</AlertDescription>
          </Alert>
        ) : null}
        {historyQuery.isError ? (
          <Alert variant="destructive">
            <AlertTitle>Could not load history</AlertTitle>
            <AlertDescription>
              {historyQuery.error instanceof Error
                ? historyQuery.error.message
                : "Unknown error"}
            </AlertDescription>
          </Alert>
        ) : null}
        <ScrollArea className="min-h-0 flex-1 rounded-md border bg-muted/20 p-3">
          <div className="space-y-3 pr-2">
            {!messages.length && !streaming && !historyQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">
                Ask about roles, interview prep, or how to improve your resume.
              </p>
            ) : null}
            {messages.map((m, i) => (
              <div
                key={`${i}-${m.role}`}
                className={
                  m.role === "user"
                    ? "ml-8 rounded-lg bg-primary/10 px-3 py-2 text-sm"
                    : "mr-8 rounded-lg border bg-card px-3 py-2 text-sm"
                }
              >
                <p className="text-xs font-medium uppercase text-muted-foreground">
                  {m.role}
                </p>
                <p className="mt-1 whitespace-pre-wrap">{m.content}</p>
              </div>
            ))}
            {streaming ? (
              <div className="mr-8 rounded-lg border bg-card px-3 py-2 text-sm">
                <p className="text-xs font-medium uppercase text-muted-foreground">
                  assistant
                </p>
                <p className="mt-1 whitespace-pre-wrap">{streaming}</p>
              </div>
            ) : null}
            {historyQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading history…</p>
            ) : null}
          </div>
        </ScrollArea>
        <div className="flex shrink-0 gap-2">
          <Textarea
            rows={2}
            placeholder="Message your mentor…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            disabled={busy || historyBlocking}
            className="min-h-[72px] resize-none"
          />
          <Button
            type="button"
            className="self-end"
            size="icon"
            disabled={busy || historyBlocking || !input.trim()}
            onClick={() => void send()}
            aria-label="Send"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
