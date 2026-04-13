export const queryKeys = {
  session: ["session"] as const,
  profile: (userId: string) => ["profile", "users", userId] as const,
  chatHistory: (sessionId: string) => ["chat-history", sessionId] as const,
  report: (reportId: string) => ["report", reportId] as const,
};
