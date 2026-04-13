import { CareerChatPanel } from "@/components/chat/career-chat-panel";

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Mentor chat</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Messages stream from <code className="text-xs">POST /chat</code> with{" "}
          <code className="text-xs">stream: true</code>.
        </p>
      </div>
      <CareerChatPanel />
    </div>
  );
}
