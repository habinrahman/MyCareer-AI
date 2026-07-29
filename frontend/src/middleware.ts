import { type NextRequest, NextResponse } from "next/server";

const MAIN_PATH = "/tools/resume-intelligence";

const LEGACY_PREFIXES = [
  "/dashboard",
  "/resume",
  "/chat",
  "/reports",
  "/analysis",
  "/careers",
  "/settings",
  "/auth",
] as const;

function isLegacyPath(pathname: string): boolean {
  return LEGACY_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/" || isLegacyPath(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = MAIN_PATH;
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/dashboard/:path*",
    "/resume/:path*",
    "/chat/:path*",
    "/reports/:path*",
    "/analysis/:path*",
    "/careers/:path*",
    "/settings/:path*",
    "/auth/:path*",
  ],
};
