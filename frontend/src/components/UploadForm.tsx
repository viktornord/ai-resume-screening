import { FileText, Loader2, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { screenResumes } from "@/api/client";
import type { ScreenResponse } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const ACCEPT = ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

interface Props {
  onResult: (result: ScreenResponse) => void;
  onError: (message: string) => void;
}

export function UploadForm({ onResult, onError }: Props) {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumes, setResumes] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const jdRef = useRef<HTMLInputElement>(null);
  const resumeRef = useRef<HTMLInputElement>(null);

  const canSubmit = jdFile && resumes.length > 0 && !loading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jdFile || resumes.length === 0) return;
    setLoading(true);
    onError("");
    try {
      const result = await screenResumes(jdFile, resumes);
      onResult(result);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Screening failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setJdFile(null);
    setResumes([]);
    if (jdRef.current) jdRef.current.value = "";
    if (resumeRef.current) resumeRef.current.value = "";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload documents</CardTitle>
        <CardDescription>
          One job description (PDF or DOCX) and up to 20 resumes.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-2 block text-sm font-medium">Job description</label>
            <input
              ref={jdRef}
              type="file"
              accept={ACCEPT}
              className="block w-full text-sm file:mr-4 file:rounded-md file:border-0 file:bg-muted file:px-4 file:py-2 file:text-sm file:font-medium"
              onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
            />
            {jdFile && (
              <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                <FileText className="h-3 w-3" />
                {jdFile.name}
              </p>
            )}
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">Resumes</label>
            <input
              ref={resumeRef}
              type="file"
              accept={ACCEPT}
              multiple
              className="block w-full text-sm file:mr-4 file:rounded-md file:border-0 file:bg-muted file:px-4 file:py-2 file:text-sm file:font-medium"
              onChange={(e) =>
                setResumes(e.target.files ? Array.from(e.target.files) : [])
              }
            />
            {resumes.length > 0 && (
              <ul className="mt-2 space-y-0.5 text-xs text-muted-foreground">
                {resumes.map((f) => (
                  <li key={f.name + f.size} className="flex items-center gap-1">
                    <FileText className="h-3 w-3" />
                    {f.name}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={!canSubmit}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Screening…
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Screen resumes
                </>
              )}
            </Button>
            <Button type="button" variant="outline" onClick={reset} disabled={loading}>
              Clear
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
