const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "https://moinsystems-ai-chatbot-production-3e00.up.railway.app";

export interface SessionResponse {
  session_id: number;
  session_token: string;
  status: string;
}

export interface ChatRequest {
  session_token: string;
  question: string;
  recent_messages?: Array<{
    role: string;
    content: string;
  }>;
}

export interface ChatResponse {
  answer: string;
  grounded: boolean;
  session_token: string;
  intent: string;
  lead_state: string;
}

export interface LeadCaptureRequest {
  session_token: string;
  full_name?: string | null;
  email?: string | null;
  contact_number?: string | null;
  company_name?: string | null;
  project_summary?: string | null;
  service_interest?: string | null;
  timeline?: string | null;
  budget_range?: string | null;
  source_page?: string | null;
  conversation_summary?: string | null;
}

export interface LeadCaptureResponse {
  session_token: string;
  state: string;
  message: string;
}

const MAX_RETRIES = 2;
const RETRY_DELAY = 800;

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  let lastError: unknown;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(options.headers ?? {}),
        },
      });

      if (!response.ok) {
        let message = "Something went wrong. Please try again.";

        try {
          const errorData = await response.json();

          if (Array.isArray(errorData?.detail)) {
            message = "Please check your information and try again.";
          } else if (typeof errorData?.detail === "string") {
            message = errorData.detail;
          }
        } catch {
          // Keep fallback message.
        }

        if (response.status >= 500 && attempt < MAX_RETRIES) {
          await wait(RETRY_DELAY * (attempt + 1));
          continue;
        }

        throw new Error(message);
      }

      return (await response.json()) as T;
    } catch (error) {
      lastError = error;

      if (
        error instanceof Error &&
        error.message !== "Failed to fetch"
      ) {
        throw error;
      }

      if (attempt < MAX_RETRIES) {
        await wait(RETRY_DELAY * (attempt + 1));
        continue;
      }
    }
  }

  if (lastError instanceof Error) {
    throw lastError;
  }

  throw new Error(
    "Unable to connect to the server. Please try again.",
  );
}

export async function createSession(
  sourcePage?: string,
): Promise<SessionResponse> {
  const query = sourcePage
    ? `?source_page=${encodeURIComponent(sourcePage)}`
    : "";

  return request<SessionResponse>(
    `/api/v1/sessions${query}`,
    {
      method: "POST",
    },
  );
}

export async function sendChatMessage(
  payload: ChatRequest,
): Promise<ChatResponse> {
  return request<ChatResponse>(
    "/api/v1/chat/messages",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function captureLead(
  payload: LeadCaptureRequest,
): Promise<LeadCaptureResponse> {
  return request<LeadCaptureResponse>(
    "/api/v1/lead-capture",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}