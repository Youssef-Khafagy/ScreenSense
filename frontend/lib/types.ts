export interface AttentionRegion {
  x:         number;
  y:         number;
  intensity: number;
  label:     string;
}

export interface AttentionScores {
  top_region:       string;
  attention_spread: number;
  peak_intensity:   number;
}

export interface PredictionResult {
  heatmap_base64:    string;
  overlay_base64:    string;
  raw_map_base64:    string;
  scores:            AttentionScores;
  attention_regions: AttentionRegion[];
  attention_grid:    number[][];
  processing_time_s: number;
  image_size:        { width: number; height: number };
}

export type ViewMode = "original" | "overlay" | "heatmap" | "side-by-side";
