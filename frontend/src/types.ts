export interface Classification {
  incident_type: string;
  relevance: string;
  severity: number | null;
  confidence: number;
  abstained: boolean;
  reasoning_summary: string | null;
  model_name: string;
  prompt_version: string;
}

export interface IncidentSummary {
  id: number;
  source: string;
  url: string;
  title: string;
  published_at: string | null;
  ingested_at: string;
  classification: Classification | null;
}

export interface Review {
  id: number;
  classification_id: number;
  reviewer: string;
  decision: string;
  notes: string | null;
  reviewed_at: string;
}

export interface IncidentDetail extends IncidentSummary {
  body: string;
  classifications: Classification[];
  reviews: Review[];
}

export interface Page {
  items: IncidentSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface Stats {
  total_incidents: number;
  total_classified: number;
  abstention_rate: number;
  by_incident_type: Record<string, number>;
}
