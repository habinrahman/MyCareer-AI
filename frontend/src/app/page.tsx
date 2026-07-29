import { redirect } from "next/navigation";

/** Public MVP: MicroDegree resume intelligence is the only surface. */
export default function HomePage() {
  redirect("/tools/resume-intelligence");
}
