import axios from 'axios';

const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach studio password header and handle FormData
api.interceptors.request.use((config) => {
  const pwd = localStorage.getItem('pactory_studio_password');
  if (pwd) {
    config.headers['x-studio-password'] = pwd;
  }
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  return config;
});

// Response interceptor to catch 401s
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('pactory:unauthorized'));
    }
    return Promise.reject(err);
  }
);

export default api;

// -------------------------------------------------------------
// Typed API Services
// -------------------------------------------------------------

export const authApi = {
  getStatus: () => api.get<{ auth_required: boolean }>('/api/auth/status').then((r) => r.data),
  login: (password: string) =>
    api.post<{ authenticated: boolean; message: string }>('/api/auth/login', { password }).then((r) => r.data),
};

export interface InboxFileItem {
  filename: string;
  size_bytes: number;
  extension: string;
  is_indexed: boolean;
  doc_id?: string;
}

export interface InboxScanResponse {
  total_files: number;
  unindexed_files: number;
  files: InboxFileItem[];
  skipped_duplicates: any[];
}

export interface ArticleSummaryItem {
  doc_id: string;
  title: string;
  author: string;
  published_date: string;
  source_format: string;
  char_count: number;
  image_count: number;
  status: string;
  primary_category?: string;
  article_archetype?: string;
  core_thesis?: string;
  reusable_asset_types?: string[];
  target_audience?: string;
  core_problem?: string;
  reframing_logic?: string;
  hook_strategy?: string;
  solution_framework?: string[];
  notable_episodes?: string[];
  topic_tags?: string[];
  ingested_at?: string;
  indexed_at?: string;
}

export interface VisualAssetItem {
  doc_id?: string;
  doc_title?: string;
  asset_id: string;
  asset_type?: string;
  page_no?: number;
  file_path: string;
  image_url?: string;
  width?: number;
  height?: number;
  caption?: string;
}

export interface ArticleDetailResponse {
  article: ArticleSummaryItem;
  visual_assets: VisualAssetItem[];
  preview_text: string;
  full_text?: string;
}

export interface JobStatusResponse {
  job_id: string;
  job_type: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'PARTIAL_SUCCESS' | 'FAILED';
  total_items: number;
  processed_items: number;
  failed_items: number;
  current_doc_id: string;
  log_summary: string;
  started_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface InboxProcessResponse {
  processed_count: number;
  indexed_count: number;
  skipped_count: number;
  job_id?: string;
  status: string;
  message: string;
}

export const inboxApi = {
  scan: () => api.get<InboxScanResponse>('/api/inbox/scan').then((r) => r.data),
  uploadFiles: (files: File[]) => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    return api.post<{ uploaded_count: number; saved_files: string[]; message: string }>(
      '/api/inbox/upload',
      formData
    ).then((r) => r.data);
  },
  process: (force = false, moveArchive = true) =>
    api.post<InboxProcessResponse>('/api/inbox/process', { force, move_archive: moveArchive }).then((r) => r.data),
  getActiveJob: () => api.get<JobStatusResponse | null>('/api/inbox/jobs/active').then((r) => r.data),
  getJobStatus: (jobId: string) => api.get<JobStatusResponse>(`/api/inbox/jobs/${jobId}`).then((r) => r.data),
  listArticles: (limit = 50, status?: string) =>
    api.get<{ total: number; items: ArticleSummaryItem[] }>('/api/inbox/articles', { params: { limit, status } }).then((r) => r.data),
  getArticleDetail: (docId: string) =>
    api.get<ArticleDetailResponse>(`/api/inbox/articles/${docId}`).then((r) => r.data),
  getStats: () => api.get('/api/inbox/stats').then((r) => r.data),
};

export interface SeedCandidateItem {
  doc_id: string;
  title: string;
  archetype: string;
  target_audience: string;
  core_thesis: string;
  solution_framework: string[];
  notable_episodes: string[];
  topic_tags: string[];
  relevance_score: number;
  assigned_role?: string;
}

export interface BlueprintResponse {
  working_title: string;
  core_thesis: string;
  target_audience: string;
  hook_strategy: string;
  key_framework: string[];
  outline_sections: any[];
  selected_seed_ids: string[];
  raw_blueprint: any;
}

export interface DraftSynthesizeResponse {
  title: string;
  content: string;
  char_count: number;
  topic: string;
  direction: string;
  seed_doc_ids: string[];
  creation_id?: string;
}

export interface RandomInspirationResponse {
  topic: string;
  direction: string;
  target_archetype: string;
  concept_summary: string;
  selected_seeds: SeedCandidateItem[];
}

export const draftApi = {
  getRandomInspiration: (preferred_category?: string, count = 3, model?: string) =>
    api
      .post<RandomInspirationResponse>('/api/draft/random-inspiration', {
        preferred_category,
        count,
        model,
      })
      .then((r) => r.data),
  searchSeeds: (topic: string, direction = '', limit = 10) =>
    api
      .post<{ topic: string; direction: string; total_found: number; candidates: SeedCandidateItem[] }>(
        '/api/draft/seeds',
        { topic, direction, limit }
      )
      .then((r) => r.data),
  generateBlueprint: (
    topic: string,
    direction = '',
    archetype = 'PRACTICAL_GUIDE',
    selected_seed_ids: string[] = [],
    model?: string
  ) =>
    api
      .post<BlueprintResponse>('/api/draft/blueprint', {
        topic,
        direction,
        target_archetype: archetype,
        selected_seed_ids,
        model,
      })
      .then((r) => r.data),
  synthesize: (
    topic: string,
    direction = '',
    archetype = 'PRACTICAL_GUIDE',
    selected_seed_ids: string[] = [],
    blueprint: any = {},
    target_length = 2500,
    model?: string
  ) =>
    api
      .post<DraftSynthesizeResponse>('/api/draft/synthesize', {
        topic,
        direction,
        target_archetype: archetype,
        selected_seed_ids,
        blueprint,
        target_length,
        model,
      })
      .then((r) => r.data),
  getSeedAssets: (seedIds: string[]) =>
    api
      .get<{ total: number; assets: VisualAssetItem[] }>(`/api/draft/assets?seed_ids=${seedIds.join(',')}`)
      .then((r) => r.data),
  getSeedDetail: (docId: string) =>
    api.get<ArticleDetailResponse>(`/api/draft/seeds/${docId}`).then((r) => r.data),
};

export interface CreationSummaryItem {
  creation_id: string;
  topic: string;
  direction: string;
  target_archetype: string;
  status: string;
  created_at: string;
  finalized_at?: string;
  has_final: boolean;
  title: string;
  seed_doc_ids: string[];
}

export interface CreationDetailResponse {
  creation_id: string;
  topic: string;
  direction: string;
  target_archetype: string;
  ai_draft_text: string;
  user_final_text: string;
  custom_notes: string;
  status: string;
  seed_doc_ids: string[];
  created_at: string;
  finalized_at?: string;
}

export interface ProofreadResponse {
  platform: string;
  mode: string;
  critique_report: string;
  rewritten_text?: string;
  hooking_score: number;
  balance_score: number;
  platform_score: number;
  suggested_title: string;
}

export const editorApi = {
  listCreations: (status?: string, limit = 50) =>
    api.get<CreationSummaryItem[]>('/api/creations', { params: { status, limit } }).then((r) => r.data),
  getCreation: (id: string) => api.get<CreationDetailResponse>(`/api/creations/${id}`).then((r) => r.data),
  saveCreation: (payload: any) => api.post<CreationDetailResponse>('/api/creations', payload).then((r) => r.data),
  updateCreation: (id: string, payload: { user_final_text: string; custom_notes?: string; status?: string }) =>
    api.put<CreationDetailResponse>(`/api/creations/${id}`, payload).then((r) => r.data),
  deleteCreation: (id: string) => api.delete<{ success: boolean; message: string }>(`/api/creations/${id}`).then((r) => r.data),
  proofread: (payload: {
    content: string;
    platform?: string;
    mode?: string;
    custom_instruction?: string;
    critique_feedback?: string;
    metadata_context?: string;
    model?: string;
  }) => api.post<ProofreadResponse>('/api/proofread', payload).then((r) => r.data),
  getCreationAssets: (creationId: string) =>
    api.get<{ total: number; assets: VisualAssetItem[] }>(`/api/creations/${creationId}/assets`).then((r) => r.data),
};

export interface StyleProfileResponse {
  persona_name: string;
  tone_and_manner: string[];
  sentence_style: Record<string, any>;
  vocabulary_profile: Record<string, any>;
  storytelling_structures: string[];
  banned_patterns: string[];
  raw_profile: Record<string, any>;
}

export const styleApi = {
  getStyle: () => api.get<StyleProfileResponse>('/api/style').then((r) => r.data),
  updateStyle: (profile_data: any) => api.put<StyleProfileResponse>('/api/style', { profile_data }).then((r) => r.data),
  learnStyle: (min_finalized_count = 1, force = false, window_size = 10) =>
    api.post<{ success: boolean; learned_creations_count: number; updated_profile: any; message: string }>('/api/style/learn', {
      min_finalized_count,
      force,
      window_size,
    }).then((r) => r.data),
};

export interface ObservabilityStats {
  total_calls: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  avg_latency_ms: number;
  total_cost_usd: number;
}

export const observabilityApi = {
  getStats: () => api.get<ObservabilityStats>('/api/observability/stats').then((r) => r.data),
};

