/**
 * API client communicating with SmartGuide FastAPI backend.
 */

import type { HealthResponse, StructuredTroubleshootResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function checkBackendHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }

  return response.json();
}

export async function troubleshootQuery(
  query: string,
  debug: boolean = true
): Promise<StructuredTroubleshootResponse> {
  const url = new URL(`${API_BASE_URL}/troubleshoot`);
  if (debug) {
    url.searchParams.append('debug', 'true');
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Troubleshoot API failed (${response.status}): ${errorBody || response.statusText}`);
  }

  return response.json();
}
