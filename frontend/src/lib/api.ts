const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (typeof window !== "undefined") {
    const token = localStorage.getItem("prospect_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `Erro ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (typeof errorJson.detail === "string") {
        errorMsg = errorJson.detail;
      } else if (Array.isArray(errorJson.detail)) {
        errorMsg = errorJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
      } else if (errorJson.message) {
        errorMsg = typeof errorJson.message === "string" ? errorJson.message : JSON.stringify(errorJson.message);
      } else if (errorJson.detail) {
        errorMsg = JSON.stringify(errorJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

export const api = {
  // Auth
  login: (formData: URLSearchParams) =>
    fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    }).then(r => {
      if (!r.ok) throw new Error("Credenciais inválidas");
      return r.json();
    }),

  getMe: () => fetchApi<any>("/auth/me"),

  // Dashboard
  getDashboard: () => fetchApi<any>("/dashboard"),

  // Extrator
  createExtractionJob: (data: any) =>
    fetchApi<any>("/extraction", { method: "POST", body: JSON.stringify(data) }),
  listExtractionJobs: () => fetchApi<any[]>("/extraction"),
  getExtractionJob: (id: number) => fetchApi<any>(`/extraction/${id}`),
  importExtractedLeads: (jobId: number, data: { selected_indices: number[]; campaign_id?: number }) =>
    fetchApi<any>(`/extraction/${jobId}/import`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Leads
  listLeads: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") q.append(k, String(v));
    });
    return fetchApi<any>(`/leads?${q.toString()}`);
  },
  getLeadDetails: (id: number) => fetchApi<any>(`/leads/${id}`),
  createLead: (data: any) => fetchApi<any>("/leads", { method: "POST", body: JSON.stringify(data) }),
  updateLead: (id: number, data: any) => fetchApi<any>(`/leads/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  bulkLeadAction: (data: any) => fetchApi<any>("/leads/bulk", { method: "POST", body: JSON.stringify(data) }),

  // Campanhas
  listCampaigns: () => fetchApi<any[]>("/campaigns"),
  createCampaign: (data: any) => fetchApi<any>("/campaigns", { method: "POST", body: JSON.stringify(data) }),
  getCampaign: (id: number) => fetchApi<any>(`/campaigns/${id}`),
  updateCampaign: (id: number, data: any) => fetchApi<any>(`/campaigns/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  campaignAction: (id: number, action: string) =>
    fetchApi<any>(`/campaigns/${id}/action`, { method: "POST", body: JSON.stringify({ action }) }),
  dispatchCampaignNow: (id: number) =>
    fetchApi<any>(`/campaigns/${id}/dispatch`, { method: "POST" }),
  triggerMessageGeneration: (id: number) =>
    fetchApi<any>(`/campaigns/${id}/generate-messages`, { method: "POST" }),
  getCampaignLeads: (id: number) => fetchApi<any[]>(`/campaigns/${id}/leads`),
  getCampaignMessages: (id: number) => fetchApi<any[]>(`/campaigns/${id}/messages`),
  updateMessageContent: (messageId: number, finalContent: string) =>
    fetchApi<any>(`/campaigns/messages/${messageId}`, {
      method: "PUT",
      body: JSON.stringify({ final_content: finalContent }),
    }),

  // IA
  testAiConnection: (provider: string, apiKey?: string) =>
    fetchApi<any>("/ai/test-connection", {
      method: "POST",
      body: JSON.stringify({ provider, api_key: apiKey }),
    }),

  // Evolution WhatsApp
  testEvolutionConnection: (data: { url?: string; api_key?: string; instance?: string; provider?: string }) =>
    fetchApi<any>("/evolution/test-connection", {
      method: "POST",
      body: JSON.stringify({ provider: "evolution", ...data }),
    }),

  // Google Places
  testGooglePlacesConnection: (apiKey?: string) =>
    fetchApi<any>("/settings/test-google-places", {
      method: "POST",
      body: JSON.stringify({ api_key: apiKey }),
    }),

  // Conversas & Atendimento
  listConversations: (status?: string) => {
    const q = status ? `?status=${status}` : "";
    return fetchApi<any[]>(`/conversations${q}`);
  },
  getConversationDetail: (id: number) => fetchApi<any>(`/conversations/${id}`),
  sendConversationReply: (id: number, message: string) =>
    fetchApi<any>(`/conversations/${id}/reply`, {
      method: "POST",
      body: JSON.stringify({ message_content: message }),
    }),
  updateConversationStatus: (id: number, status: string) =>
    fetchApi<any>(`/conversations/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    }),
  optOutConversation: (id: number) =>
    fetchApi<any>(`/conversations/${id}/opt-out`, { method: "POST" }),

  // Relatórios
  getReports: () => fetchApi<any>("/reports"),
  getExportCsvUrl: () => `${API_BASE_URL}/reports/export-csv`,

  // Configurações
  getSettings: () => fetchApi<any>("/settings"),
  updateSettings: (settingsObj: Record<string, any>) =>
    fetchApi<any>("/settings", {
      method: "PUT",
      body: JSON.stringify({ settings: settingsObj }),
    }),

  // Automação Contínua de Prospecção (Novo Arquitetura)
  getAutomationStatus: () => fetchApi<any>("/automation/status"),
  toggleAutomationStatus: (status: string) =>
    fetchApi<any>("/automation/toggle", {
      method: "POST",
      body: JSON.stringify({ status }),
    }),
  getAutomationPrompt: () => fetchApi<any>("/automation/prompt"),
  updateAutomationPrompt: (prompt: string) =>
    fetchApi<any>("/automation/prompt", {
      method: "PUT",
      body: JSON.stringify({ prompt }),
    }),
  resetAutomationPrompt: () =>
    fetchApi<any>("/automation/prompt/reset", { method: "POST" }),
  simulateMessage: (payload: {
    company_name: string;
    website_url?: string;
    contact_name?: string;
    city?: string;
    notes?: string;
    custom_prompt?: string;
  }) =>
    fetchApi<any>("/automation/simulate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getAutomationSettings: () => fetchApi<any>("/automation/settings"),
  updateAutomationSettings: (payload: any) =>
    fetchApi<any>("/automation/settings", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  getAutomationStats: () => fetchApi<any>("/automation/stats"),
  getAutomationQueue: () => fetchApi<any>("/automation/queue"),
  removeLeadFromQueue: (leadId: number) =>
    fetchApi<any>(`/automation/queue/${leadId}`, { method: "DELETE" }),
  dispatchAutomationNow: () =>
    fetchApi<any>("/automation/dispatch-now", { method: "POST" }),
  getAutomationHistory: () => fetchApi<any>("/automation/history"),
};
