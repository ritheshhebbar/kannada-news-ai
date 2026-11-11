export interface Source {
  id: number;
  name: string;
  base_url: string;
  feed_url?: string;
  robots_checked: boolean;
  terms_note?: string;
  active: boolean;
}

export interface Category {
  id: number;
  slug: string;
  name_en: string;
  name_kn: string;
}

export interface SentenceTranslation {
  translation_id: number;
  sentence_id: number;
  text_en: string;
  labse_sim?: number;
  qe_score?: number;
  flags: Array<{ type: string; detail: string; severity?: string }>;
}

export interface Sentence {
  id: number;
  idx: number;
  paragraph_idx: number;
  text_kn: string;
  translation?: SentenceTranslation;
}

export interface Translation {
  id: number;
  article_id: number;
  backend: string;
  model_version: string;
  title_en?: string;
  guard_report?: any;
  is_active: boolean;
  sentences: SentenceTranslation[];
}

export interface KeyPoint {
  text: string;
  evidence: number[];
}

export interface KeyFacts {
  who: string[];
  what: string[];
  where: string[];
  when: string[];
  numbers: string[];
}

export interface Summary {
  id: number;
  article_id: number;
  model: string;
  method: "llm" | "extractive_fallback";
  headline_en?: string;
  summary_en?: string;
  key_points?: KeyPoint[];
  key_facts?: KeyFacts;
  verification?: any;
}

export interface Entity {
  id: number;
  lang: "kn" | "en";
  text: string;
  norm_text?: string;
  type: string;
  sentence_idx?: number;
}

export interface ArticleListItem {
  id: number;
  origin: string;
  url?: string;
  title_kn?: string;
  title_en?: string;
  two_line_summary?: string;
  section_label?: string;
  published_at?: string;
  status: string;
  source_name?: string;
  has_flags: boolean;
}

export interface ArticleDetail {
  id: number;
  source_id?: number;
  source_name?: string;
  origin: string;
  url?: string;
  title_kn?: string;
  title_en?: string;
  body_kn: string;
  section_label?: string;
  published_at?: string;
  status: string;
  session_id?: string;
  sentences: Sentence[];
  active_translation?: Translation;
  active_summary?: Summary;
  entities: Entity[];
  categories: Category[];
  flags: Array<{ sentence_idx: number; type: string; detail: string }>;
}

export interface DashboardStats {
  articles_today: number;
  translated_count: number;
  flagged_for_review: number;
  average_latency_sec: number;
  items_in_queue: number;
  verification_pass_rate: number;
  categories_distribution: Record<string, number>;
}

export interface ArticleAskResponse {
  article_id: number;
  question: string;
  answer: string;
  cited_sentences: number[];
  grounded: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function getSessionId(): string {
  if (typeof window === "undefined") return "server-session";
  let sid = localStorage.getItem("kannada_news_session_id");
  if (!sid) {
    sid = "sess_" + Math.random().toString(36).substring(2, 12);
    localStorage.setItem("kannada_news_session_id", sid);
  }
  return sid;
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error: ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  getArticles: (params?: { source_id?: number; category?: string; status?: string; search?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.source_id) q.append("source_id", params.source_id.toString());
    if (params?.category) q.append("category", params.category);
    if (params?.status) q.append("status", params.status);
    if (params?.search) q.append("search", params.search);
    if (params?.page) q.append("page", params.page.toString());
    if (params?.page_size) q.append("page_size", params.page_size.toString());
    return request<{ items: ArticleListItem[]; total: number; page: number; total_pages: number }>(`/articles?${q.toString()}`);
  },

  getArticle: (id: number) => request<ArticleDetail>(`/articles/${id}`),

  submitArticle: (data: { text?: string; url?: string; title?: string; section_label?: string; session_id?: string }) =>
    request<{ article_id: number; job_id?: number; status: string; message: string }>("/articles/submit", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getArticleStatus: (id: number) =>
    request<{ article_id: number; status: string; current_stage?: string; progress: number; last_error?: string }>(`/articles/${id}/status`),

  retryArticle: (id: number) =>
    request<{ status: string; article_id: number }>(`/articles/${id}/retry`, { method: "POST" }),

  search: (query: string, sessionId?: string, page: number = 1) => {
    const q = new URLSearchParams({ q: query, page: page.toString() });
    if (sessionId) q.append("session_id", sessionId);
    return request<{ query: string; items: ArticleListItem[]; total: number }>(`/search?${q.toString()}`);
  },

  getStats: () => request<DashboardStats>("/stats"),
  getCategories: () => request<Category[]>("/categories"),
  getSources: () => request<Source[]>("/sources"),

  getBookmarks: (sessionId: string) => request<ArticleListItem[]>(`/bookmarks?session_id=${sessionId}`),
  addBookmark: (sessionId: string, articleId: number) =>
    request("/bookmarks", { method: "POST", body: JSON.stringify({ session_id: sessionId, article_id: articleId }) }),
  removeBookmark: (sessionId: string, articleId: number) =>
    request(`/bookmarks/${articleId}?session_id=${sessionId}`, { method: "DELETE" }),

  getReadingHistory: (sessionId: string) => request<any[]>(`/history/reading?session_id=${sessionId}`),
  recordReading: (sessionId: string, articleId: number) =>
    request(`/history/reading/${articleId}?session_id=${sessionId}`, { method: "POST" }),
  getSearchHistory: (sessionId: string) => request<any[]>(`/history/search?session_id=${sessionId}`),
  clearHistory: (sessionId: string) => request(`/history/clear?session_id=${sessionId}`, { method: "POST" }),

  submitFeedback: (data: { article_id: number; sentence_id?: number; kind: string; comment?: string }) =>
    request("/feedback", { method: "POST", body: JSON.stringify(data) }),

  askArticle: (articleId: number, question: string, sessionId?: string) =>
    request<ArticleAskResponse>(`/articles/${articleId}/ask`, {
      method: "POST",
      body: JSON.stringify({ question, session_id: sessionId }),
    }),
};
