export const RISK_TIERS = {
  low:      { label: 'LOW RISK',  color: '#00E676', bg: 'bg-risk-low/10',      border: 'border-risk-low/30',      text: 'text-risk-low' },
  medium:   { label: 'MEDIUM',    color: '#FFD740', bg: 'bg-risk-medium/10',   border: 'border-risk-medium/30',   text: 'text-risk-medium' },
  high:     { label: 'HIGH RISK', color: '#FF6D00', bg: 'bg-risk-high/10',     border: 'border-risk-high/30',     text: 'text-risk-high' },
  distress: { label: 'DISTRESS',  color: '#D500F9', bg: 'bg-risk-distress/10', border: 'border-risk-distress/30', text: 'text-risk-distress' },
}

export const DOC_TYPES = [
  { value: 'annual_report',    label: 'Annual Report' },
  { value: 'earnings_call',    label: 'Earnings Call' },
  { value: 'credit_agreement', label: 'Credit Agreement' },
  { value: 'other',            label: 'Other' },
]

export const AGENTS = [
  { key: 'Document Parser',  label: 'DOCUMENT PARSER',  desc: 'Extracting text and indexing chunks into vector database' },
  { key: 'Ratio Extractor',  label: 'RATIO EXTRACTOR',  desc: 'LLaMA 3.1 extracting financial ratios from document' },
  { key: 'Sentiment Analyst',label: 'SENTIMENT ANALYST',desc: 'FinBERT analyzing financial tone across all sections' },
  { key: 'Breach Detector',  label: 'BREACH DETECTOR',  desc: 'Scanning for covenant violations and risk flags' },
  { key: 'Risk Scorer',      label: 'RISK SCORER',      desc: 'XGBoost computing credit risk score with SHAP explainability' },
  { key: 'Report Writer',    label: 'REPORT WRITER',    desc: 'GPT-4 composing the final credit risk advisory report' },
]

export const ROLES = {
  admin:     { label: 'ADMIN',    color: 'text-crimson border-crimson/30 bg-crimson/10' },
  analyst:   { label: 'ANALYST',  color: 'text-electric-light border-electric/30 bg-electric/10' },
  viewer:    { label: 'VIEWER',   color: 'text-ink-secondary border-ink-muted/30 bg-surface-raised' },
  superadmin:{ label: 'SUPER',    color: 'text-risk-distress border-risk-distress/30 bg-risk-distress/10' },
}