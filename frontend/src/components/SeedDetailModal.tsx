import { useState, useEffect } from 'react';
import {
  X,
  BookOpen,
  Sparkles,
  Copy,
  Check,
  CheckCircle2,
  Image as ImageIcon,
  Tag,
  Loader2,
  FileText,
  Calendar,
  User,
  Hash,
} from 'lucide-react';
import { draftApi } from '../api/client';
import type { ArticleDetailResponse, VisualAssetItem } from '../api/client';

const ARCHETYPE_LABELS: Record<string, string> = {
  PRACTICAL_GUIDE: '실무 가이드 / 튜토리얼',
  step_by_step_tutorial: '단계별 튜토리얼',
  trial_and_error_retro: '시행착오 회고',
  framework_checklist: '프레임워크 / 체크리스트',
  case_study_workshop: '다중 사례 워크숍',
  brand_interview_qa: '브랜드 인터뷰 / Q&A',
  template_curation: '템플릿 / 도구 큐레이션',
  THEORETICAL_DEEP_DIVE: '심층 분석 / 이론 고찰',
  OPINION_ESSAY: '오피니언 / 주장 에세이',
};

interface SeedDetailModalProps {
  docId: string | null;
  isOpen: boolean;
  onClose: () => void;
  isSelected?: boolean;
  onToggleSelect?: (docId: string) => void;
}

export const SeedDetailModal = ({
  docId,
  isOpen,
  onClose,
  isSelected = false,
  onToggleSelect,
}: SeedDetailModalProps) => {
  const [detail, setDetail] = useState<ArticleDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [activeTab, setActiveTab] = useState<'text' | 'summary' | 'assets'>('text');
  const [copied, setCopied] = useState(false);
  const [lightboxImage, setLightboxImage] = useState<VisualAssetItem | null>(null);

  useEffect(() => {
    if (!isOpen || !docId) {
      setDetail(null);
      setErrorMsg('');
      setActiveTab('text');
      setLightboxImage(null);
      return;
    }

    const fetchDetail = async () => {
      setIsLoading(true);
      setErrorMsg('');
      try {
        const data = await draftApi.getSeedDetail(docId);
        setDetail(data);
      } catch (err: any) {
        setErrorMsg(err.response?.data?.detail || '시드 원문 데이터를 불러오지 못했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetail();
  }, [isOpen, docId]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        if (lightboxImage) {
          setLightboxImage(null);
        } else {
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, lightboxImage, onClose]);

  if (!isOpen || !docId) return null;

  const handleCopyText = () => {
    const textToCopy = detail?.full_text || detail?.preview_text || '';
    if (!textToCopy) return;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const article = detail?.article;
  const visualAssets = detail?.visual_assets || [];
  const textContent = detail?.full_text || detail?.preview_text || '';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-start justify-between bg-slate-50/80">
          <div className="space-y-1.5 pr-4 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 bg-indigo-100 text-indigo-700 font-mono font-bold text-xs rounded-md">
                <Hash className="w-3 h-3" />
                <span>{docId}</span>
              </span>
              {article?.primary_category && (
                <span className="px-2.5 py-0.5 bg-blue-50 text-blue-700 text-xs font-semibold rounded-md border border-blue-100">
                  {article.primary_category}
                </span>
              )}
              {article?.article_archetype && (
                <span className="px-2.5 py-0.5 bg-purple-50 text-purple-700 text-xs font-semibold rounded-md border border-purple-100">
                  {ARCHETYPE_LABELS[article.article_archetype] || article.article_archetype}
                </span>
              )}
              {onToggleSelect && (
                <span
                  className={`inline-flex items-center space-x-1 px-2.5 py-0.5 text-xs font-bold rounded-md ${
                    isSelected
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {isSelected ? (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>선택된 소재</span>
                    </>
                  ) : (
                    <span>미선택</span>
                  )}
                </span>
              )}
            </div>

            <h2 className="text-xl font-extrabold text-slate-900 leading-snug">
              {article?.title || `문서 #${docId}`}
            </h2>

            <div className="text-xs text-slate-400 flex flex-wrap items-center gap-x-3 gap-y-1 pt-0.5">
              {article?.author && (
                <span className="inline-flex items-center space-x-1">
                  <User className="w-3 h-3 text-slate-400" />
                  <span>{article.author}</span>
                </span>
              )}
              {article?.published_date && (
                <span className="inline-flex items-center space-x-1">
                  <Calendar className="w-3 h-3 text-slate-400" />
                  <span>{article.published_date}</span>
                </span>
              )}
              <span>{article?.char_count ? `${article.char_count.toLocaleString()}자` : `${textContent.length.toLocaleString()}자`}</span>
              {article?.source_format && (
                <span className="uppercase text-[11px] font-semibold bg-slate-200/80 text-slate-700 px-1.5 py-0.2 rounded">
                  {article.source_format}
                </span>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-lg transition-colors"
            title="닫기 (ESC)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 border-b border-slate-200 bg-white flex items-center justify-between">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab('text')}
              className={`flex items-center space-x-1.5 py-3 px-3.5 border-b-2 text-xs font-bold transition-colors ${
                activeTab === 'text'
                  ? 'border-indigo-600 text-indigo-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>원문 전문</span>
              {textContent && (
                <span className="ml-1 text-[11px] font-normal text-slate-400">
                  ({textContent.length.toLocaleString()}자)
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('summary')}
              className={`flex items-center space-x-1.5 py-3 px-3.5 border-b-2 text-xs font-bold transition-colors ${
                activeTab === 'summary'
                  ? 'border-indigo-600 text-indigo-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span>핵심 요약 및 메타데이터</span>
            </button>

            <button
              onClick={() => setActiveTab('assets')}
              className={`flex items-center space-x-1.5 py-3 px-3.5 border-b-2 text-xs font-bold transition-colors ${
                activeTab === 'assets'
                  ? 'border-indigo-600 text-indigo-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <ImageIcon className="w-4 h-4" />
              <span>시각 자료</span>
              <span className="ml-1 px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded-full text-[10px] font-semibold">
                {visualAssets.length}
              </span>
            </button>
          </div>

          {activeTab === 'text' && textContent && (
            <button
              onClick={handleCopyText}
              className="flex items-center space-x-1 text-xs text-slate-600 hover:text-indigo-600 px-2.5 py-1 rounded-lg border border-slate-200 hover:border-indigo-200 transition-colors"
              title="원문 전체 클립보드 복사"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-600 font-semibold">복사 완료</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>본문 복사</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="px-6 py-5 overflow-y-auto flex-1 text-xs text-slate-800">
          {isLoading && (
            <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
              <span className="text-sm font-medium">시드 원문 및 메타데이터를 불러오는 중입니다...</span>
            </div>
          )}

          {errorMsg && (
            <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl">
              {errorMsg}
            </div>
          )}

          {!isLoading && !errorMsg && detail && (
            <>
              {/* TAB 1: FULL TEXT */}
              {activeTab === 'text' && (
                <div className="space-y-4">
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 leading-relaxed font-sans text-sm text-slate-800 whitespace-pre-wrap select-text break-words">
                    {textContent || '등록된 원문 내용이 없습니다.'}
                  </div>
                </div>
              )}

              {/* TAB 2: STRUCTURED SUMMARY */}
              {activeTab === 'summary' && (
                <div className="space-y-6">
                  {/* Core Thesis */}
                  {article?.core_thesis && (
                    <div className="bg-indigo-50/70 border-l-4 border-indigo-600 p-4 rounded-r-xl space-y-1">
                      <div className="text-[11px] font-bold text-indigo-900 flex items-center space-x-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                        <span>핵심 테제 (Core Thesis)</span>
                      </div>
                      <p className="text-slate-800 text-sm font-semibold leading-relaxed">
                        "{article.core_thesis}"
                      </p>
                    </div>
                  )}

                  {/* Reframing & Target Audience Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1.5">
                      <span className="font-bold text-slate-700 text-xs block">🎯 타깃 독자 & 핵심 문제</span>
                      <p className="text-slate-600 text-xs leading-relaxed">
                        <strong>독자:</strong> {article?.target_audience || '미지정'}
                      </p>
                      {article?.core_problem && (
                        <p className="text-slate-600 text-xs leading-relaxed">
                          <strong>핵심 결핍/문제:</strong> {article.core_problem}
                        </p>
                      )}
                    </div>

                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1.5">
                      <span className="font-bold text-slate-700 text-xs block">💡 관점 전환 명제 (Reframing)</span>
                      <p className="text-slate-600 text-xs leading-relaxed">
                        {article?.reframing_logic || '별도 관점 전환 명제 없음'}
                      </p>
                      {article?.hook_strategy && (
                        <p className="text-slate-500 text-[11px] pt-1">
                          <strong>도입부 훅:</strong> {article.hook_strategy}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Solution Framework */}
                  {article?.solution_framework && article.solution_framework.length > 0 && (
                    <div className="space-y-2">
                      <span className="font-bold text-slate-700 text-xs block">
                        🛠️ 핵심 솔루션 프레임워크 (실행 단계)
                      </span>
                      <div className="grid grid-cols-1 gap-2">
                        {article.solution_framework.map((step, idx) => (
                          <div
                            key={idx}
                            className="flex items-start space-x-2.5 p-3 bg-white border border-slate-200 rounded-xl"
                          >
                            <span className="flex-shrink-0 w-5 h-5 bg-indigo-100 text-indigo-700 font-bold rounded-full flex items-center justify-center text-[11px]">
                              {idx + 1}
                            </span>
                            <span className="text-xs text-slate-700 font-medium leading-relaxed">
                              {step}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Notable Episodes */}
                  {article?.notable_episodes && article.notable_episodes.length > 0 && (
                    <div className="space-y-2">
                      <span className="font-bold text-slate-700 text-xs block">
                        📌 주목할 만한 구체적 에피소드 & 실화
                      </span>
                      <ul className="list-disc list-inside space-y-1.5 text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200">
                        {article.notable_episodes.map((ep, i) => (
                          <li key={i} className="leading-relaxed">
                            {ep}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Topic Tags */}
                  {article?.topic_tags && article.topic_tags.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
                        <Tag className="w-3.5 h-3.5 text-slate-500" />
                        <span>추출 토픽 키워드 태그</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {article.topic_tags.map((tag, i) => (
                          <span
                            key={i}
                            className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: VISUAL ASSETS */}
              {activeTab === 'assets' && (
                <div className="space-y-4">
                  {visualAssets.length === 0 ? (
                    <div className="py-16 text-center text-slate-400">
                      <ImageIcon className="w-10 h-10 mx-auto mb-2 text-slate-300 stroke-1" />
                      <p>추출된 이미지나 도표 시각 자료가 없습니다.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                      {visualAssets.map((asset, idx) => (
                        <div
                          key={idx}
                          onClick={() => setLightboxImage(asset)}
                          className="group border border-slate-200 rounded-xl overflow-hidden bg-slate-50 cursor-pointer hover:border-indigo-400 hover:shadow-md transition-all flex flex-col"
                        >
                          <div className="aspect-video bg-slate-200 relative overflow-hidden flex items-center justify-center">
                            {asset.image_url ? (
                              <img
                                src={asset.image_url}
                                alt={asset.caption || asset.asset_id}
                                className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-200"
                                onError={(e) => {
                                  (e.target as HTMLElement).style.display = 'none';
                                }}
                              />
                            ) : (
                              <FileText className="w-8 h-8 text-slate-400" />
                            )}
                            <div className="absolute inset-0 bg-slate-900/0 group-hover:bg-slate-900/20 transition-colors flex items-center justify-center">
                              <span className="opacity-0 group-hover:opacity-100 bg-slate-900/80 text-white text-[10px] font-bold px-2 py-1 rounded-md transition-opacity">
                                크게 보기
                              </span>
                            </div>
                          </div>
                          <div className="p-2.5 space-y-1 flex-1 flex flex-col justify-between">
                            <div>
                              <div className="font-semibold text-slate-800 truncate text-[11px]">
                                {asset.asset_id}
                              </div>
                              {asset.caption && (
                                <p className="text-[10px] text-slate-500 line-clamp-2 mt-0.5 leading-snug">
                                  {asset.caption}
                                </p>
                              )}
                            </div>
                            <div className="text-[9px] text-slate-400 pt-1 border-t border-slate-100 flex items-center justify-between">
                              <span>p.{asset.page_no || 1}</span>
                              {asset.width && asset.height && (
                                <span>{asset.width}x{asset.height}</span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-slate-100 flex items-center justify-between bg-slate-50/80">
          <span className="text-xs text-slate-500">
            문서 번호: <code className="font-mono font-bold text-indigo-600">#{docId}</code>
          </span>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-slate-200 hover:bg-slate-100 rounded-xl text-xs font-semibold text-slate-700 transition-colors"
            >
              닫기
            </button>

            {onToggleSelect && (
              <button
                type="button"
                onClick={() => onToggleSelect(docId)}
                className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-xs ${
                  isSelected
                    ? 'bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-600/20'
                }`}
              >
                {isSelected ? (
                  <>
                    <X className="w-3.5 h-3.5" />
                    <span>소재 선택 해제</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>이 소재를 초안에 포함하기</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Lightbox for visual asset */}
      {lightboxImage && (
        <div
          className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs animate-in fade-in"
          onClick={() => setLightboxImage(null)}
        >
          <div
            className="max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden flex flex-col p-4 space-y-3"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between text-white border-b border-slate-800 pb-2">
              <span className="text-xs font-semibold">{lightboxImage.asset_id}</span>
              <button
                onClick={() => setLightboxImage(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-auto flex items-center justify-center">
              <img
                src={lightboxImage.image_url}
                alt={lightboxImage.caption || lightboxImage.asset_id}
                className="max-w-full max-h-[70vh] object-contain rounded-lg"
              />
            </div>
            {lightboxImage.caption && (
              <p className="text-xs text-slate-300 text-center leading-relaxed">
                {lightboxImage.caption}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
