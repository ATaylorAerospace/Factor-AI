export interface RiskScore {
  provision_id: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  score: number;
  factors: string[];
  explanation: string;
  is_synthetic: boolean;
  document_id?: string;
}

export interface GapResult {
  document_id: string;
  missing_provision: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  recommendation: string;
  reference_standard: string;
  is_synthetic: boolean;
}

export interface ComparisonResult {
  provision_type: string;
  documents_compared: string[];
  inconsistencies: string[];
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  count: number;
}

export interface ReportSection {
  title: string;
  items: Record<string, unknown>[];
  synthetic_content: boolean;
}

export interface Report {
  title: string;
  generated_at: string;
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  executive_summary: string;
  disclaimer: string;
  synthetic_dataset_used: boolean;
  sections: ReportSection[];
}

export interface TraceEntry {
  agent: string;
  action: string;
  timestamp: number;
  details: Record<string, unknown>;
}

export interface AnalysisState {
  status: 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error';
  files: File[];
  progress: number;
  report: Report | null;
  trace: TraceEntry[];
  sessionId: string | null;
  error: string | null;
}

export interface Session {
  session_id: string;
  status: string;
  document_count: number;
  created_at: string;
  disclaimer: string;
}

export interface KnowledgeResult {
  content: string;
  legal_domain: string;
  source: string;
  is_synthetic: boolean;
  disclaimer: string;
  score: number | null;
}

export interface Domain {
  name: string;
  is_due_diligence: boolean;
}
