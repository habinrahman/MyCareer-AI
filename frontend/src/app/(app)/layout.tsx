import { AppSectionLayout } from "@/components/layout/app-section-layout";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppSectionLayout>{children}</AppSectionLayout>;
}
