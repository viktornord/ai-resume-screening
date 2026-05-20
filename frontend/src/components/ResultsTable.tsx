import type { ScreenResponse } from "@/api/types";
import { CandidateRow } from "@/components/CandidateRow";
import { RequirementsBanner } from "@/components/RequirementsBanner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Download } from "lucide-react";

interface Props {
  result: ScreenResponse;
}

export function ResultsTable({ result }: Props) {
  const exportJson = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `screening-${result.screened_at.slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <RequirementsBanner
        jobTitle={result.job_title_hint}
        reasoning={result.requirements_reasoning}
        ambiguities={result.requirements_ambiguities}
      />

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Ranked candidates</CardTitle>
            <CardDescription>
              {result.candidates.length} resume
              {result.candidates.length !== 1 ? "s" : ""} screened in{" "}
              {(result.processing_ms / 1000).toFixed(1)}s
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={exportJson}>
            <Download className="h-4 w-4" />
            Export JSON
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {result.candidates.length === 0 ? (
            <p className="px-6 pb-6 text-sm text-muted-foreground">
              No candidates returned.
            </p>
          ) : (
            <div>
              {result.candidates.map((c, i) => (
                <CandidateRow key={c.source_filename + i} candidate={c} rank={i + 1} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
