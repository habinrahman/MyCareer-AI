import Link from "next/link";
import { ArrowRight } from "lucide-react";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const tiles = [
  {
    href: "/resume",
    title: "Upload resume",
    description: "Parse and run structured analysis on your latest CV.",
  },
  {
    href: "/chat",
    title: "Mentor chat",
    description: "Ask for interview prep, role fit, and improvement ideas.",
  },
  {
    href: "/reports",
    title: "Reports",
    description: "Reopen past runs and download PDF career reports.",
  },
  {
    href: "/careers",
    title: "Career insights",
    description: "Resume intelligence: benchmarks, learning-focused job match, and mentor link.",
  },
];

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="mt-2 text-muted-foreground">
          Pick up where you left off. Everything here uses your Supabase session
          and the FastAPI backend configured in{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            NEXT_PUBLIC_API_URL
          </code>
          .
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map((t) => (
          <Link key={t.href} href={t.href} className="group block">
            <Card className="h-full transition-shadow group-hover:shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-lg">
                  {t.title}
                  <ArrowRight className="h-4 w-4 opacity-0 transition-opacity group-hover:opacity-100" />
                </CardTitle>
                <CardDescription>{t.description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
