import { useEffect, useState } from "react";
import { checkHealth } from "@/api/client";
import type { HealthResponse, ScreenResponse } from "@/api/types";
import { ResultsTable } from "@/components/ResultsTable";
import { UploadForm } from "@/components/UploadForm";
import { Badge } from "@/components/ui/badge";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [result, setResult] = useState<ScreenResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() =>
        setHealth({
          status: "unreachable",
          llm_reachable: false,
          model_ready: false,
        }),
      );
  }, []);

  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-background">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-5">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              AI Resume Screening
            </h1>
            <p className="text-sm text-muted-foreground">
              Upload a job description and resumes to rank candidates.
            </p>
          </div>
          {health && (
            <div className="flex flex-col items-end gap-1">
              <Badge
                variant={
                  health.status === "ok" && health.model_ready
                    ? "success"
                    : "warning"
                }
              >
                {health.status === "ok" && health.model_ready
                  ? "LLM ready"
                  : health.llm_reachable
                    ? "Mistral reachable"
                    : "LLM offline"}
              </Badge>
              <span className="text-xs text-muted-foreground">
                Mistral {health.llm_reachable ? "reachable" : "unreachable"}
              </span>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-8 px-4 py-8">
        <UploadForm
          onResult={(r) => {
            setResult(r);
            setError("");
          }}
          onError={setError}
        />

        {error && (
          <div
            role="alert"
            className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          >
            {error}
          </div>
        )}

        {result && <ResultsTable result={result} />}
      </main>
    </div>
  );
}
