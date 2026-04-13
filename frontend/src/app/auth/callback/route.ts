import { NextResponse } from "next/server";
import { safeNextPath } from "@/lib/auth/paths";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const next = safeNextPath(requestUrl.searchParams.get("next"));

  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
    return NextResponse.redirect(
      new URL("/auth/login?error=config", requestUrl.origin),
    );
  }

  if (code) {
    try {
      const supabase = createSupabaseServerClient();
      const { error } = await supabase.auth.exchangeCodeForSession(code);
      if (!error) {
        return NextResponse.redirect(new URL(next, requestUrl.origin));
      }
    } catch {
      return NextResponse.redirect(
        new URL("/auth/login?error=auth", requestUrl.origin),
      );
    }
  }

  return NextResponse.redirect(
    new URL("/auth/login?error=auth", requestUrl.origin),
  );
}
