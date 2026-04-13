export type ReportDetailResponse = {
  id: string;
  title: string;
  report_type: string;
  status: string;
  storage_path?: string | null;
  signed_url?: string | null;
  analysis_id?: string | null;
};
