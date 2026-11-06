import { useState, useEffect, useRef } from 'react';
import {
  Database,
  RefreshCw,
  CheckCircle2,
  FileText,
  UploadCloud,
  X,
  AlertCircle,
  Eye,
  Tag,
  Sparkles,
  Layers,
  Image as ImageIcon,
  Users,
  BookOpen,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { inboxApi } from '../api/client';
import type { ArticleSummaryItem, InboxScanResponse, ArticleDetailResponse, JobStatusResponse } from '../api/client';

const ARCHETYPE_LABELS: Record<string, string> = {
  step_by_step_tutorial: '단계별 튜토리얼',
  trial_and_error_retro: '시행착오 회고',
  framework_checklist: '프레임워크/체크리스트',
  case_study_workshop: '다중 사례 워크숍',
  brand_interview_qa: '브랜드 인터뷰/Q&A',
  template_curation: '템플릿/도구 큐레이션',
};

const ASSET_TYPE_LABELS: Record<string, string> = {
  prompt_template: '프롬프트',
  checklist_table: '체크리스트',
  before_after_comparison: '비교표',
  quantitative_metrics: '정량수치',
  failure_episode: '실패사례',
  step_diagram: '프로세스도식',
};

export const InboxPage = () => {
  const [scanData, setScanData] = useState<InboxScanResponse | null>(null);
  const [articles, setArticles] = useState<ArticleSummaryItem[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processMessage, setProcessMessage] = useState('');

  // Policy 2: Job-based Background Queue State
  const [activeJob, setActiveJob] = useState<JobStatusResponse | null>(null);
  const pollingTimerRef = useRef<any>(null);

  // Drag and Drop Upload States
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Detail Modal States
  const [selectedArticle, setSelectedArticle] = useState<ArticleSummaryItem | null>(null);
  const [articleDetail, setArticleDetail] = useState<ArticleDetailResponse | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const loadData = async () => {
    setIsScanning(true);
    try {
      const [scanRes, articlesRes, statsRes] = await Promise.allSettled([
        inboxApi.scan(),
        inboxApi.listArticles(500),
        inboxApi.getStats(),
      ]);
      if (scanRes.status === 'fulfilled') setScanData(scanRes.value);
      if (articlesRes.status === 'fulfilled') setArticles(articlesRes.value.items);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value);
    } catch (err) {
      console.error(err);
    } finally {
      setIsScanning(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    try {
      const status = await inboxApi.getJobStatus(jobId);
      setActiveJob(status);
      if (['COMPLETED', 'PARTIAL_SUCCESS', 'FAILED'].includes(status.status)) {
        if (pollingTimerRef.current) {
          clearInterval(pollingTimerRef.current);
          pollingTimerRef.current = null;
        }
        setIsProcessing(false);
        setProcessMessage(status.log_summary || `작업 완료 (${status.status})`);
        await loadData();
      }
    } catch (err) {
      console.error('Job polling error:', err);
    }
  };

  const startJobPolling = (jobId: string) => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
    }
    setIsProcessing(true);
    pollJobStatus(jobId);
    pollingTimerRef.current = setInterval(() => {
      pollJobStatus(jobId);
    }, 1500);
  };

  const checkActiveJob = async () => {
    try {
      const running = await inboxApi.getActiveJob();
      if (running) {
        setActiveJob(running);
        startJobPolling(running.job_id);
      }
    } catch (err) {
      console.error('Failed to check active job:', err);
    }
  };

  useEffect(() => {
    loadData();
    checkActiveJob();

    // Prevent default browser file-opening on drop outside dropzone
    const handleWindowDragOver = (e: DragEvent) => e.preventDefault();
    const handleWindowDrop = (e: DragEvent) => e.preventDefault();

    window.addEventListener('dragover', handleWindowDragOver);
    window.addEventListener('drop', handleWindowDrop);

    return () => {
      window.removeEventListener('dragover', handleWindowDragOver);
      window.removeEventListener('drop', handleWindowDrop);
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
      }
    };
  }, []);

  const handleProcess = async () => {
    setIsProcessing(true);
    setProcessMessage('색인 파이프라인 작업을 큐에 등록하는 중입니다...');
    try {
      // Policy 1: moveArchive=true (Keep inbox as pure queue), Policy 2: Async 202 Accepted Job queue
      const res = await inboxApi.process(false, true);
      setProcessMessage(res.message);
      if (res.job_id) {
        startJobPolling(res.job_id);
      } else {
        await loadData();
        setIsProcessing(false);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || '색인 요청 중 오류가 발생했습니다.');
      setIsProcessing(false);
    }
  };

  const filterSupportedFiles = (files: FileList | File[]): File[] => {
    const supportedExts = ['.pdf', '.md', '.txt', '.docx'];
    const valid: File[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (supportedExts.includes(ext)) {
        valid.push(file);
      }
    }
    return valid;
  };

  // Immediate Auto-Upload on Drop or File Selection
  const executeUpload = async (files: File[]) => {
    if (files.length === 0) return;
    setIsUploading(true);
    setUploadMessage(null);
    try {
      const res = await inboxApi.uploadFiles(files);
      setUploadMessage({
        type: 'success',
        text: res.message || `${files.length}개 파일이 inbox에 성공적으로 업로드되었습니다.`,
      });
      await loadData();
    } catch (err: any) {
      setUploadMessage({
        type: 'error',
        text: err.response?.data?.detail || '파일 업로드 중 오류가 발생했습니다.',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const valid = filterSupportedFiles(e.dataTransfer.files);
      if (valid.length === 0) {
        setUploadMessage({
          type: 'error',
          text: '지원되는 파일 형식(.pdf, .md, .txt, .docx)만 업로드할 수 있습니다.',
        });
        return;
      }
      await executeUpload(valid);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const valid = filterSupportedFiles(e.target.files);
      if (valid.length > 0) {
        await executeUpload(valid);
      }
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Open Article Detail Modal
  const handleOpenDetail = async (art: ArticleSummaryItem) => {
    setSelectedArticle(art);
    setIsLoadingDetail(true);
    try {
      const detail = await inboxApi.getArticleDetail(art.doc_id);
      setArticleDetail(detail);
    } catch (err) {
      console.error('Failed to load full detail, using summary:', err);
      setArticleDetail({
        article: art,
        visual_assets: [],
        preview_text: '',
      });
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedArticle(null);
    setArticleDetail(null);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Banner */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-xs flex items-start space-x-4">
        <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 text-indigo-400">
          <Database className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h2 className="font-bold text-base">소재 색인 관리 (Knowledge Index Manager)</h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            신규 문서(PDF, Markdown, TXT, DOCX)를 드래그앤드롭하여 서버로 직접 업로드하고 자동 색인 파이프라인을 실행합니다. 색인된 아티클의 핵심 테제, 구조, 고유 에셋, 추출 이미지 및 키워드는 카탈로그 DB에 영구 보존되어 새 글 작성 시 보완적 시드로 활용됩니다.
          </p>
        </div>
      </div>

      {/* Summary Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">인박스 대기 파일</span>
          <div className="text-2xl font-extrabold text-slate-900 mt-1">
            {scanData?.total_files || 0}
            <span className="text-xs font-normal text-slate-500 ml-1.5">
              (미색인: {scanData?.unindexed_files || 0})
            </span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">DB 색인 완료 아티클</span>
          <div className="text-2xl font-extrabold text-indigo-600 mt-1">
            {stats?.indexed_articles || 0}
            <span className="text-xs font-normal text-slate-500 ml-1.5">편</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">누적 생성 아티클</span>
          <div className="text-2xl font-extrabold text-emerald-600 mt-1">
            {stats?.total_creations || 0}
            <span className="text-xs font-normal text-slate-500 ml-1.5">편</span>
          </div>
        </div>
      </div>

      {/* Browser Drag & Drop Upload Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
              <UploadCloud className="w-4 h-4 text-indigo-600" />
              <span>신규 문서 브라우저 직접 추가 (Drag & Drop)</span>
            </h3>
            <p className="text-[11px] text-slate-400">
              PDF, DOCX, TXT, 마크다운(MD) 문서를 영역에 끌어다 놓으면 <strong>별도 클릭 없이 즉시 서버 data/inbox/로 자동 업로드</strong>됩니다.
            </p>
          </div>
        </div>

        {/* Upload Status Banner */}
        {uploadMessage && (
          <div
            className={`p-3 rounded-xl text-xs flex items-center justify-between transition-all ${
              uploadMessage.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-rose-50 text-rose-800 border border-rose-200'
            }`}
          >
            <div className="flex items-center space-x-2">
              {uploadMessage.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span>{uploadMessage.text}</span>
            </div>
            <button
              onClick={() => setUploadMessage(null)}
              className="text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Drop Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-indigo-600 bg-indigo-50/70 scale-[1.01]'
              : isUploading
              ? 'border-amber-400 bg-amber-50/40 cursor-wait'
              : 'border-slate-300 hover:border-indigo-500 hover:bg-slate-50/70'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            multiple
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            disabled={isUploading}
          />
          <div className="flex flex-col items-center justify-center space-y-2.5">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
                isDragging
                  ? 'bg-indigo-600 text-white'
                  : isUploading
                  ? 'bg-amber-100 text-amber-600 animate-pulse'
                  : 'bg-indigo-50 text-indigo-600'
              }`}
            >
              {isUploading ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <UploadCloud className="w-6 h-6" />
              )}
            </div>
            <div className="text-sm font-semibold text-slate-800">
              {isUploading ? (
                <span className="text-amber-700">문서를 서버로 전송 중입니다...</span>
              ) : isDragging ? (
                <span className="text-indigo-600">파일을 여기에 놓으면 즉시 업로드됩니다!</span>
              ) : (
                <>
                  문서 파일을 여기에 끌어다 놓거나{' '}
                  <span className="text-indigo-600 underline font-bold">클릭하여 파일 선택</span>
                </>
              )}
            </div>
            <p className="text-xs text-slate-400">
              지원 형식: .pdf, .docx, .txt, .md (드래그앤드롭 즉시 자동 전송 및 수신 목록 갱신)
            </p>
          </div>
        </div>
      </div>

      {/* Inbox File Processing Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">인박스 대기 파일 목록 (data/inbox/)</h3>
            <p className="text-[11px] text-slate-400">
              업로드된 파일 중 미색인 문서를 카탈로그 DB로 추출 및 인덱싱합니다.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadData}
              disabled={isScanning}
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
              title="새로고침"
            >
              <RefreshCw className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={handleProcess}
              disabled={isProcessing || !scanData?.unindexed_files}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs"
            >
              <CheckCircle2 className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
              <span>{isProcessing ? '색인 처리 중...' : '미색인 파일 일괄 색인 실행'}</span>
            </button>
          </div>
        </div>

        {/* Policy 2: Real-time Job Progress Indicator */}
        {activeJob && (
          <div className="bg-slate-900 text-white rounded-xl p-4 shadow-xs space-y-3 border border-slate-800">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <Loader2 className={`w-4 h-4 text-indigo-400 ${activeJob.status === 'RUNNING' ? 'animate-spin' : ''}`} />
                <span className="font-bold text-slate-100">
                  {activeJob.status === 'RUNNING' ? '백그라운드 색인 파이프라인 처리 중' : `작업 상태: ${activeJob.status}`}
                </span>
                <span className="text-slate-400 font-mono text-[11px]">({activeJob.job_id})</span>
              </div>
              <div className="text-right font-mono font-bold text-indigo-300">
                {activeJob.total_items > 0
                  ? `${Math.round((activeJob.processed_items / activeJob.total_items) * 100)}% (${activeJob.processed_items}/${activeJob.total_items}건)`
                  : `${activeJob.processed_items}건 완료`}
              </div>
            </div>

            {/* Progress Bar Track */}
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${
                    activeJob.total_items > 0
                      ? Math.min(100, Math.round((activeJob.processed_items / activeJob.total_items) * 100))
                      : activeJob.status === 'COMPLETED'
                      ? 100
                      : 25
                  }%`,
                }}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <div className="truncate max-w-[80%] flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                <span className="text-slate-300 truncate">{activeJob.log_summary || '데이터 파이프라인 동기화 중...'}</span>
              </div>
              {activeJob.failed_items > 0 && (
                <span className="text-rose-400 font-bold shrink-0">실패 {activeJob.failed_items}건</span>
              )}
            </div>
          </div>
        )}

        {processMessage && !activeJob && (
          <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl text-xs text-indigo-900 font-medium">
            {processMessage}
          </div>
        )}

        {scanData?.files && scanData.files.length > 0 ? (
          <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
            {scanData.files.map((f, idx) => (
              <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-slate-800">{f.filename}</span>
                  <span className="text-[11px] text-slate-400">({(f.size_bytes / 1024).toFixed(1)} KB)</span>
                </div>
                <div>
                  {f.is_indexed ? (
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-md text-[11px] font-bold">
                      색인 완료 (#{f.doc_id})
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded-md text-[11px] font-bold">
                      대기 중 (미색인)
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-400">
            inbox 폴더에 처리 대기 중인 파일이 없습니다. 상단에서 파일을 드래그앤드롭하여 업로드해 보세요.
          </div>
        )}
      </div>

      {/* Indexed Articles Catalog Table */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">색인 카탈로그 대장 (총 {articles.length}편)</h3>
            <p className="text-[11px] text-slate-400">
              추출된 카테고리, 아키타입, 핵심 테제, 키워드 및 고유 에셋 정보입니다. <strong>행을 클릭하면 전체 분석 모달</strong>이 열립니다.
            </p>
          </div>
          <button
            onClick={loadData}
            disabled={isScanning}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/50">
                <th className="py-2.5 px-3 font-semibold w-16">ID</th>
                <th className="py-2.5 px-3 font-semibold min-w-[200px]">제목</th>
                <th className="py-2.5 px-3 font-semibold w-24">카테고리</th>
                <th className="py-2.5 px-3 font-semibold w-28">아키타입</th>
                <th className="py-2.5 px-3 font-semibold min-w-[220px]">핵심 테제 요약</th>
                <th className="py-2.5 px-3 font-semibold min-w-[150px]">키워드 태그</th>
                <th className="py-2.5 px-3 font-semibold w-28">고유 에셋/이미지</th>
                <th className="py-2.5 px-3 font-semibold w-16 text-center">상세</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {articles.map((art) => (
                <tr
                  key={art.doc_id}
                  onClick={() => handleOpenDetail(art)}
                  className="hover:bg-indigo-50/60 cursor-pointer transition-colors group"
                >
                  <td className="py-3 px-3 font-mono font-bold text-indigo-600 align-top">
                    #{art.doc_id}
                  </td>
                  <td className="py-3 px-3 font-medium text-slate-900 align-top">
                    <div className="group-hover:text-indigo-600 font-semibold transition-colors">
                      {art.title}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5 flex items-center space-x-1.5">
                      <span>{art.char_count.toLocaleString()}자</span>
                      <span>·</span>
                      <span className="uppercase">{art.source_format}</span>
                      {art.image_count > 0 && (
                        <>
                          <span>·</span>
                          <span className="text-indigo-500 font-medium">📷 이미지 {art.image_count}개</span>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-3 align-top">
                    {art.primary_category ? (
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-md text-[11px] font-semibold">
                        {art.primary_category}
                      </span>
                    ) : (
                      <span className="text-slate-300">-</span>
                    )}
                  </td>
                  <td className="py-3 px-3 align-top">
                    {art.article_archetype ? (
                      <span className="px-2 py-0.5 bg-purple-50 text-purple-700 rounded-md text-[11px] font-semibold">
                        {ARCHETYPE_LABELS[art.article_archetype] || art.article_archetype}
                      </span>
                    ) : (
                      <span className="text-slate-300">-</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-700 align-top">
                    {art.core_thesis ? (
                      <p className="line-clamp-2 leading-relaxed text-[11px]" title={art.core_thesis}>
                        {art.core_thesis}
                      </p>
                    ) : (
                      <span className="text-slate-300">-</span>
                    )}
                  </td>
                  <td className="py-3 px-3 align-top">
                    {art.topic_tags && art.topic_tags.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {art.topic_tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-medium"
                          >
                            #{tag}
                          </span>
                        ))}
                        {art.topic_tags.length > 3 && (
                          <span className="text-[10px] text-slate-400">+{art.topic_tags.length - 3}</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-300">-</span>
                    )}
                  </td>
                  <td className="py-3 px-3 align-top">
                    <div className="flex flex-col gap-1">
                      {art.reusable_asset_types && art.reusable_asset_types.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {art.reusable_asset_types.slice(0, 2).map((t, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 bg-amber-50 text-amber-800 rounded text-[10px] font-medium"
                            >
                              {ASSET_TYPE_LABELS[t] || t}
                            </span>
                          ))}
                          {art.reusable_asset_types.length > 2 && (
                            <span className="text-[10px] text-slate-400">
                              +{art.reusable_asset_types.length - 2}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-300">-</span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-3 align-top text-center">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenDetail(art);
                      }}
                      className="p-1 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      title="상세 모달 열기"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {articles.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400 text-xs">
                    색인된 아티클이 없습니다. 상단에서 파일을 업로드하고 색인을 진행해 보세요.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Article Detail Modal */}
      {selectedArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div
            className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex items-start justify-between bg-slate-50/70">
              <div className="space-y-1 pr-6">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 font-mono font-bold text-xs rounded-md">
                    #{selectedArticle.doc_id}
                  </span>
                  {selectedArticle.primary_category && (
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-semibold rounded-md">
                      {selectedArticle.primary_category}
                    </span>
                  )}
                  {selectedArticle.article_archetype && (
                    <span className="px-2 py-0.5 bg-purple-50 text-purple-700 text-xs font-semibold rounded-md">
                      {ARCHETYPE_LABELS[selectedArticle.article_archetype] || selectedArticle.article_archetype}
                    </span>
                  )}
                  <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-md">
                    {selectedArticle.status}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 leading-snug">
                  {selectedArticle.title}
                </h3>
                <div className="text-xs text-slate-400 flex items-center space-x-2 pt-0.5">
                  <span>{selectedArticle.author || '저자 미상'}</span>
                  <span>·</span>
                  <span>{selectedArticle.char_count.toLocaleString()}자</span>
                  <span>·</span>
                  <span className="uppercase">{selectedArticle.source_format}</span>
                  <span>·</span>
                  <span>색인: {selectedArticle.indexed_at ? selectedArticle.indexed_at.split('T')[0] : '완료'}</span>
                </div>
              </div>
              <button
                onClick={handleCloseDetail}
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="px-6 py-5 overflow-y-auto space-y-6 flex-1 text-xs">
              {isLoadingDetail && (
                <div className="py-12 flex flex-col items-center justify-center space-y-2 text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
                  <span>색인 상세 정보 및 추출 자산을 불러오는 중...</span>
                </div>
              )}

              {/* 1. Core Thesis Highlight */}
              {selectedArticle.core_thesis && (
                <div className="bg-indigo-50/70 border-l-4 border-indigo-600 p-4 rounded-r-xl space-y-1">
                  <div className="text-[11px] font-bold text-indigo-900 flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                    <span>핵심 테제 요약 (Core Thesis)</span>
                  </div>
                  <p className="text-slate-800 text-sm font-medium leading-relaxed">
                    "{selectedArticle.core_thesis}"
                  </p>
                </div>
              )}

              {/* 2. Topic Tags */}
              {selectedArticle.topic_tags && selectedArticle.topic_tags.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
                    <Tag className="w-3.5 h-3.5 text-slate-500" />
                    <span>추출 키워드 / 토픽 태그</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedArticle.topic_tags.map((tag, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 rounded-lg text-xs font-medium transition-colors"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Audience, Problem & Reframing Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 space-y-2">
                  <div className="font-bold text-slate-800 flex items-center space-x-1.5">
                    <Users className="w-3.5 h-3.5 text-slate-500" />
                    <span>타겟 독자 & 핵심 문제의식</span>
                  </div>
                  <div className="space-y-1 text-slate-600">
                    <p>
                      <strong className="text-slate-800">타겟층:</strong>{' '}
                      {selectedArticle.target_audience || '일반 독자'}
                    </p>
                    <p>
                      <strong className="text-slate-800">핵심 결핍/문제:</strong>{' '}
                      {selectedArticle.core_problem || '명시되지 않음'}
                    </p>
                  </div>
                </div>

                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 space-y-2">
                  <div className="font-bold text-slate-800 flex items-center space-x-1.5">
                    <Layers className="w-3.5 h-3.5 text-slate-500" />
                    <span>관점 전환(Reframing) & 후킹 전략</span>
                  </div>
                  <div className="space-y-1 text-slate-600">
                    <p>
                      <strong className="text-slate-800">관점 전환:</strong>{' '}
                      {selectedArticle.reframing_logic || '명시되지 않음'}
                    </p>
                    <p>
                      <strong className="text-slate-800">도입부 훅:</strong>{' '}
                      {selectedArticle.hook_strategy || '명시되지 않음'}
                    </p>
                  </div>
                </div>
              </div>

              {/* 4. Solution Framework */}
              {selectedArticle.solution_framework && selectedArticle.solution_framework.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
                    <ChevronRight className="w-3.5 h-3.5 text-indigo-600" />
                    <span>해결 프레임워크 (Solution Framework)</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {selectedArticle.solution_framework.map((step, idx) => (
                      <div
                        key={idx}
                        className="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs space-y-1"
                      >
                        <span className="text-[10px] font-extrabold text-indigo-600 uppercase tracking-wider">
                          Step {idx + 1}
                        </span>
                        <p className="text-slate-800 font-medium text-xs leading-relaxed">{step}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 5. Notable Episodes */}
              {selectedArticle.notable_episodes && selectedArticle.notable_episodes.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-slate-500" />
                    <span>주목할 만한 구체적 에피소드 / 실화</span>
                  </div>
                  <ul className="list-disc list-inside space-y-1 text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-100">
                    {selectedArticle.notable_episodes.map((ep, i) => (
                      <li key={i} className="leading-relaxed">
                        {ep}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 6. Visual Assets & Reusable Assets */}
              <div className="space-y-3">
                <div className="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
                  <ImageIcon className="w-3.5 h-3.5 text-indigo-600" />
                  <span>
                    추출된 시각 자산 ({selectedArticle.image_count}개) 및 재사용 고유 에셋
                  </span>
                </div>

                <div className="flex flex-wrap gap-2">
                  {selectedArticle.reusable_asset_types && selectedArticle.reusable_asset_types.length > 0 ? (
                    selectedArticle.reusable_asset_types.map((t, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 bg-amber-50 text-amber-900 border border-amber-200/60 rounded-lg text-xs font-semibold"
                      >
                        {ASSET_TYPE_LABELS[t] || t}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-400">등록된 고유 에셋 유형 없음</span>
                  )}
                </div>

                {articleDetail?.visual_assets && articleDetail.visual_assets.length > 0 && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 pt-1">
                    {articleDetail.visual_assets.map((asset, idx) => (
                      <div
                        key={idx}
                        className="border border-slate-200 rounded-lg p-2 bg-slate-50 text-[11px] space-y-1"
                      >
                        <div className="font-semibold text-slate-800 truncate" title={asset.asset_id}>
                          {asset.asset_id}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {asset.width && asset.height ? `${asset.width}x${asset.height}px` : '이미지 자산'}
                        </div>
                        {asset.caption && (
                          <p className="text-[10px] text-slate-600 line-clamp-1" title={asset.caption}>
                            {asset.caption}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 7. Text Preview */}
              {articleDetail?.preview_text && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
                    <FileText className="w-3.5 h-3.5 text-slate-500" />
                    <span>본문 발췌 미리보기</span>
                  </div>
                  <pre className="bg-slate-900 text-slate-200 p-4 rounded-xl text-[11px] font-mono whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed border border-slate-800">
                    {articleDetail.preview_text}
                  </pre>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 border-t border-slate-100 flex items-center justify-between bg-slate-50/70">
              <span className="text-xs text-slate-400">
                선택된 Seed ID: <code className="font-mono font-bold text-indigo-600">#{selectedArticle.doc_id}</code>
              </span>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={handleCloseDetail}
                  className="px-4 py-2 border border-slate-200 hover:bg-slate-100 rounded-xl text-xs font-semibold text-slate-700 transition-colors"
                >
                  닫기
                </button>
                <button
                  type="button"
                  onClick={() => {
                    handleCloseDetail();
                    window.dispatchEvent(new CustomEvent('pactory:navigate', { detail: 'generator' }));
                  }}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>초안 생성기에서 활용하기</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
