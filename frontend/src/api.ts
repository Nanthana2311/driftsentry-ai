export interface LivenessResponse {
  status: "alive";
  service: string;
  version: string;
  environment: string;
}

export async function getLiveness(signal?: AbortSignal): Promise<LivenessResponse> {
  const response = await fetch("/api/v1/health/live", {
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  return (await response.json()) as LivenessResponse;
}
