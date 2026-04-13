import { apiClient } from "@/lib/api";
import type { ReportDetailResponse } from "@/types/report";

export async function fetchReportDetail(
  reportId: string,
): Promise<ReportDetailResponse> {
  const { data } = await apiClient.get<ReportDetailResponse>(
    `/report/${reportId}`,
  );
  return data;
}
