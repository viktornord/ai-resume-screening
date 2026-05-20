import * as Collapsible from "@radix-ui/react-collapsible";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { Candidate } from "@/api/types";
import { Badge } from "@/components/ui/badge";

const yearsMatchLabel: Record<string, string> = {
  clear: "Clear",
  not_enough: "Not enough",
  ambiguous: "Ambiguous",
  "n/a": "N/A",
};

const yearsMatchVariant: Record<string, "success" | "warning" | "muted" | "outline"> = {
  clear: "success",
  not_enough: "warning",
  ambiguous: "warning",
  "n/a": "muted",
};

interface Props {
  candidate: Candidate;
  rank: number;
}

export function CandidateRow({ candidate, rank }: Props) {
  const [open, setOpen] = useState(false);
  const isGood = candidate.recommendation === "Good fit";

  return (
    <Collapsible.Root open={open} onOpenChange={setOpen}>
      <div className="border-b border-border last:border-0">
        <Collapsible.Trigger asChild>
          <button
            type="button"
            className="flex w-full items-start gap-3 px-4 py-4 text-left hover:bg-muted/50"
          >
            <span className="mt-0.5 w-6 shrink-0 text-sm text-muted-foreground">
              #{rank}
            </span>
            {open ? (
              <ChevronDown className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
            ) : (
              <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
            )}
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{candidate.candidate_name}</span>
                <Badge variant={isGood ? "success" : "warning"}>
                  {candidate.recommendation}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {candidate.match_score}/100
                </span>
              </div>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">
                {candidate.source_filename}
              </p>
            </div>
          </button>
        </Collapsible.Trigger>

        <Collapsible.Content className="overflow-hidden">
          <div className="space-y-4 border-t border-border bg-muted/30 px-4 py-4 pl-14">
            <section>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Matching skills
              </h4>
              {candidate.matching_skills.length === 0 ? (
                <p className="text-sm text-muted-foreground">None identified</p>
              ) : (
                <ul className="space-y-2">
                  {candidate.matching_skills.map((s) => (
                    <li
                      key={s.name}
                      className="rounded-md border border-border bg-background p-3 text-sm"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium">{s.name}</span>
                        <Badge
                          variant={yearsMatchVariant[s.years_match] ?? "outline"}
                        >
                          {yearsMatchLabel[s.years_match] ?? s.years_match}
                        </Badge>
                      </div>
                      <p className="mt-1 text-muted-foreground">{s.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Not on resume
              </h4>
              {candidate.not_mentioned_skills.length === 0 ? (
                <p className="text-sm text-muted-foreground">None</p>
              ) : (
                <ul className="space-y-2">
                  {candidate.not_mentioned_skills.map((s) => (
                    <li
                      key={s.name}
                      className="rounded-md border border-dashed border-border bg-background p-3 text-sm"
                    >
                      <span className="font-medium">{s.name}</span>
                      <p className="mt-1 text-muted-foreground">{s.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Match reasoning
              </h4>
              <p className="text-sm leading-relaxed">{candidate.reasoning}</p>
            </section>

            {candidate.ambiguities.length > 0 && (
              <section>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Ambiguities
                </h4>
                <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                  {candidate.ambiguities.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        </Collapsible.Content>
      </div>
    </Collapsible.Root>
  );
}
