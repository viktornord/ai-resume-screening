import { AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface Props {
  jobTitle: string | null;
  reasoning: string;
  ambiguities: string[];
}

export function RequirementsBanner({ jobTitle, reasoning, ambiguities }: Props) {
  if (!reasoning && ambiguities.length === 0) return null;

  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardContent className="space-y-3 pt-6">
        <div>
          <p className="text-sm font-medium text-amber-900">
            Job requirements
            {jobTitle ? ` — ${jobTitle}` : ""}
          </p>
          {reasoning && (
            <p className="mt-1 text-sm text-amber-950/80">{reasoning}</p>
          )}
        </div>
        {ambiguities.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-white/60 p-3">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-amber-800">
              <AlertTriangle className="h-3.5 w-3.5" />
              JD ambiguities
            </p>
            <ul className="list-inside list-disc space-y-1 text-sm text-amber-950/90">
              {ambiguities.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
