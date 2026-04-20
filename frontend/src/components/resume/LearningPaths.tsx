"use client";

import { cn } from "@/lib/utils";

export type LearningPath = {
  title: string;
  provider?: string | null;
  rationale?: string;
};

type LearningPathsProps = {
  paths: LearningPath[];
  /** Merged onto the outer wrapper (e.g. strip border when nested in another card). */
  className?: string;
  showHeading?: boolean;
};

/**
 * Learning Paths: MicroDegree certifications only (title includes ``— MicroDegree``).
 */
export function LearningPaths({
  paths,
  className,
  showHeading = true,
}: LearningPathsProps) {
  if (!paths?.length) return null;

  return (
    <div className={cn("mt-8 border-t border-gray-100 pt-6", className)}>
      {showHeading ? (
        <h4 className="mb-3 text-xs font-bold uppercase tracking-wide text-microMuted">
          Learning paths
        </h4>
      ) : null}
      <ul className="space-y-3 text-sm">
        {paths.map((path, index) => (
          <li key={`${path.title}-${index}`} className="text-microTextSecondary">
            <span className="font-semibold text-microBlue">{path.title}</span>
            {path.provider ? (
              <span className="text-microMuted"> — {path.provider}</span>
            ) : null}
            {path.rationale ? (
              <p className="mt-1 text-microMuted">{path.rationale}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
