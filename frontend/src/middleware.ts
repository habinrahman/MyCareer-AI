import { type NextRequest, NextResponse } from "next/server";
import {
  isAuthPath,
  isProtectedPath,
  safeNextPath,
} from "@/lib/auth/paths";
import { createMiddlewareSupabaseClient } from "@/lib/supabase/middleware";

const authEnabled = process.env.NEXT_PUBLIC_ENABLE_AUTH === "true";
const workspaceEnabled = process.env.NEXT_PUBLIC_ENABLE_WORKSPACE !== "false";

function isWorkspaceShellPath(p: string): boolean {
  return (
    p === "/dashboard" ||
    p.startsWith("/dashboard/") ||
    p === "/resume" ||
    p.startsWith("/resume/") ||
    p === "/reports" ||
    p.startsWith("/reports/") ||
    p === "/analysis" ||
    p.startsWith("/analysis/") ||
    p === "/careers" ||
    p.startsWith("/careers/") ||
    p === "/chat" ||
    p.startsWith("/chat/")
  );
}

export async function middleware(request: NextRequest) {
  const { supabase, response } = createMiddlewareSupabaseClient(request);

  const { pathname } = request.nextUrl;

  if (!authEnabled) {
    if (isProtectedPath(pathname) || isAuthPath(pathname)) {
      const url = request.nextUrl.clone();
      url.pathname = "/";
      url.search = "";
      return NextResponse.redirect(url);
    }
    return response;
  }

  if (!supabase) {
    return response;
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (isProtectedPath(pathname) && !user) {
    const url = request.nextUrl.clone();
    url.pathname = "/auth/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (user && isAuthPath(pathname) && pathname !== "/auth/callback") {
    const url = request.nextUrl.clone();
    url.pathname = safeNextPath(request.nextUrl.searchParams.get("next"));
    url.search = "";
    return NextResponse.redirect(url);
  }

  if (user && !workspaceEnabled && isWorkspaceShellPath(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = "/";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
