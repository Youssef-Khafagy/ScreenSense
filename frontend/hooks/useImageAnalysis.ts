"use client";
import { useState, useCallback } from "react";
import { predictSaliency } from "@/lib/api";
import type { PredictionResult } from "@/lib/types";

type State =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "processing" }
  | { status: "done"; result: PredictionResult; previewUrl: string }
  | { status: "error"; message: string };

export function useImageAnalysis() {
  const [state, setState] = useState<State>({ status: "idle" });

  const analyse = useCallback(async (file: File) => {
    // Validate early on client side
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      setState({ status: "error", message: "Please upload a JPEG, PNG, or WebP image." });
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setState({ status: "error", message: "Image must be under 10 MB." });
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    setState({ status: "uploading" });

    try {
      setState({ status: "processing" });
      const result = await predictSaliency(file);
      setState({ status: "done", result, previewUrl });
    } catch (e: unknown) {
      setState({
        status:  "error",
        message: e instanceof Error ? e.message : "Something went wrong.",
      });
    }
  }, []);

  const reset = useCallback(() => setState({ status: "idle" }), []);

  return { state, analyse, reset };
}
