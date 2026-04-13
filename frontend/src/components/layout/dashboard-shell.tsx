"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileUp,
  MessageSquare,
  FileText,
  Menu,
  LogOut,
  UserRound,
  Briefcase,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/resume", label: "Resume", icon: FileUp },
  { href: "/chat", label: "Mentor chat", icon: MessageSquare },
  { href: "/careers", label: "Career insights", icon: Briefcase },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Account", icon: UserRound },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { signOut } = useAuth();

  function onSignOut() {
    void signOut();
  }

  const NavLinks = ({ mobile = false }: { mobile?: boolean }) => (
    <nav className={cn("flex gap-1", mobile ? "flex-col" : "flex-col px-3")}>
      {nav.map(({ href, label, icon: Icon }) => {
        const active =
          pathname === href ||
          (href !== "/dashboard" &&
            href !== "/settings" &&
            pathname.startsWith(href));
        const settingsActive =
          href === "/settings" &&
          (pathname === "/settings" || pathname.startsWith("/settings/"));
        const isActive = href === "/settings" ? settingsActive : active;
        return (
          <Link
            key={href}
            href={href}
            onClick={() => setOpen(false)}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="flex min-h-screen">
        <aside className="hidden w-56 shrink-0 border-r bg-card md:flex md:flex-col md:py-4">
          <div className="px-4 pb-4">
            <Link href="/dashboard" className="font-semibold tracking-tight">
              MyCareer AI
            </Link>
            <p className="text-xs text-muted-foreground">Career workspace</p>
          </div>
          <Separator />
          <div className="flex flex-1 flex-col py-4">
            <NavLinks />
          </div>
          <div className="mt-auto px-3">
            <Button
              variant="ghost"
              className="w-full justify-start gap-2 text-muted-foreground"
              type="button"
              onClick={onSignOut}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center justify-between border-b bg-card px-4 py-3 md:hidden">
            <Link href="/dashboard" className="font-semibold">
              MyCareer AI
            </Link>
            <Button
              variant="outline"
              size="icon"
              type="button"
              aria-label="Open menu"
              onClick={() => setOpen((o) => !o)}
            >
              <Menu className="h-4 w-4" />
            </Button>
          </header>
          {open ? (
            <div className="border-b bg-card px-4 py-3 md:hidden">
              <NavLinks mobile />
              <Button
                variant="ghost"
                className="mt-2 w-full justify-start gap-2"
                type="button"
                onClick={onSignOut}
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </Button>
            </div>
          ) : null}
          <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
