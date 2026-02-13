export interface ProjectInput {
  project_id: string;
  project_stage: string;
  building_type?: string;
  location_city?: string;
  gfa_m2?: number;
  shell_only?: boolean;
  fitout_required?: boolean;
  fitout_allowance_per_m2?: number;
}

export interface AuditLogEntry {
  timestamp: string;
  action: string;
  decision: string;
  reason: string;
  rule_id?: string;
  source?: string;
}

export interface EngineOutput {
  project_id: string;
  project_stage: string;
  selected_primary_library?: string;
  selected_secondary_library?: string;
  blocked_reason?: string;
  required_missing_inputs: string[];
  next_action: string;
  audit_log: AuditLogEntry[];
}

export interface CityValues {
  low?: number;
  high?: number;
}

export interface RateRow {
  description: string;
  unit?: string;
  city_values: Record<string, CityValues>;
  hours?: string;
  source_file: string;
  source_sheet: string;
  source_row_index: number;
}

export interface ConceptEstimateLineItem {
  description: string;
  quantity?: number;
  unit?: string;
  rate?: number;
  amount?: number;
  source_file?: string;
  source_sheet?: string;
  source_row_index?: number;
  note?: string;
}

export interface ConceptEstimate {
  project_id: string;
  base_build_cost?: number;
  fitout_cost?: number;
  subtotal?: number;
  line_items: ConceptEstimateLineItem[];
  disclaimer: string;
  audit_log: AuditLogEntry[];
}

export interface FileUploadResponse {
  file_type: string;
  filename: string;
  status: string;
  message: string;
}

export interface ConfigSummary {
  modules: string[];
  stages: string[];
  libraries: string[];
  schema_fields_count: number;
  rules_count: number;
  pricing_flow_count: number;
}
