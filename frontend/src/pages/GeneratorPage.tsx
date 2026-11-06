import { useState, useEffect } from 'react';
import {
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Circle,
  Layers,
  FileText,
  Edit,
  RotateCcw,
  Check,
  AlertCircle,
  Sparkles,
  Dices,
  Zap,
  X,
  Loader2,
  BookOpen,
  Image as ImageIcon,
  ZoomIn,
} from 'lucide-react';
import { draftApi, type RandomInspirationResponse, type VisualAssetItem } from '../api/client';
import { ModelSelector } from '../components/ModelSelector';
import { SeedDetailModal } from '../components/SeedDetailModal';
import { useDraftStore } from '../store/useDraftStore';

const ARCHETYPES = [
  {
    id: 'PRACTICAL_GUIDE',
    label: '🎯 실전 가이드',
    desc: '문제를 명확히 정의하고 실행 가능한 3~5단계 솔루션과 체크리스트 제공',
  },
  {
    id: 'FAILURE_RETROSPECTIVE',
    label: '🔄 실패/시행착오 회고',
    desc: '솔직한 실패 경험에서 출발하여 얻은 교훈과 반전 인사이트 제시',
  },
  {
    id: 'REFRAMING_ESSAY',
    label: '💡 통념 반박 & 재정의',
    desc: '업계의 맹점이나 상식을 뒤집고 새로운 가치 기준과 시각을 제시',
  },
  {
    id: 'INDUSTRY_DEEPDIVE',
    label: '📊 업계 심층 분석',
    desc: '거시적 트렌드, 데이터/비용 분석을 바탕으로 한 입체적 고찰',
  },
];

interface GeneratorPageProps {
  onOpenEditor: (creationId?: string, initialDraft?: string, topic?: string) => void;
}

export const GeneratorPage = ({ onOpenEditor }: GeneratorPageProps) => {
  const {
    step,
    topic,
    direction,
    targetArchetype,
    candidates,
    selectedSeedIds,
    blueprint,
    draftContent,
    creationId,
    isSearchingSeeds,
    isGeneratingBlueprint,
    isSynthesizing,
    inspirationModel,
    step2Model,
    step3Model,
    setStep,
    setTopic,
    setDirection,
    setTargetArchetype,
    toggleSeed,
    setSelectedSeedIds,
    setCandidates,
    setBlueprint,
    setDraftContent,
    setCreationId,
    setLoading,
    setInspirationModel,
    setStep2Model,
    setStep3Model,
    resetDraft,
  } = useDraftStore();

  const [errorMsg, setErrorMsg] = useState('');

  // -------------------------------------------------------------
  // Seed Full Text & Metadata Detail Modal
  // -------------------------------------------------------------
  const [viewingSeedDocId, setViewingSeedDocId] = useState<string | null>(null);

  // -------------------------------------------------------------
  // Visual Seed Assets & Lightbox
  // -------------------------------------------------------------
  const [visualAssets, setVisualAssets] = useState<VisualAssetItem[]>([]);
  const [selectedLightboxAsset, setSelectedLightboxAsset] = useState<VisualAssetItem | null>(null);

  useEffect(() => {
    if (selectedSeedIds.length > 0) {
      draftApi
        .getSeedAssets(selectedSeedIds)
        .then((res) => setVisualAssets(res.assets))
        .catch(() => setVisualAssets([]));
    } else {
      setVisualAssets([]);
    }
  }, [selectedSeedIds]);

  // -------------------------------------------------------------
  // Random Inspiration States & Handlers
  // -------------------------------------------------------------
  const [inspiration, setInspiration] = useState<RandomInspirationResponse | null>(null);
  const [showInspirationModal, setShowInspirationModal] = useState(false);
  const [isLoadingInspiration, setIsLoadingInspiration] = useState(false);
  const [isDirectSynthesizing, setIsDirectSynthesizing] = useState(false);

  const handleFetchRandomInspiration = async () => {
    setErrorMsg('');
    setIsLoadingInspiration(true);
    try {
      const data = await draftApi.getRandomInspiration(undefined, 3, inspirationModel);
      setInspiration(data);
      setShowInspirationModal(true);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || '랜덤 영감 생성 중 오류가 발생했습니다.');
    } finally {
      setIsLoadingInspiration(false);
    }
  };

  const handleApplyToForm = (insp: RandomInspirationResponse) => {
    setTopic(insp.topic);
    setDirection(insp.direction);
    if (insp.target_archetype) {
      setTargetArchetype(insp.target_archetype);
    }
    if (insp.selected_seeds && insp.selected_seeds.length > 0) {
      setCandidates(insp.selected_seeds);
      setSelectedSeedIds(insp.selected_seeds.map((s) => s.doc_id));
      setStep(2);
    }
    setShowInspirationModal(false);
  };

  const handleDirectSynthesize = async (insp: RandomInspirationResponse) => {
    setIsDirectSynthesizing(true);
    setErrorMsg('');
    const seedIds = insp.selected_seeds.map((s) => s.doc_id);
    const arch = insp.target_archetype || targetArchetype;

    try {
      setTopic(insp.topic);
      setDirection(insp.direction);
      setTargetArchetype(arch);
      setCandidates(insp.selected_seeds);
      setSelectedSeedIds(seedIds);

      const res = await draftApi.synthesize(
        insp.topic,
        insp.direction,
        arch,
        seedIds,
        {},
        2500,
        inspirationModel
      );

      setDraftContent(res.content);
      if (res.creation_id) {
        setCreationId(res.creation_id);
      }
      setShowInspirationModal(false);
      onOpenEditor(res.creation_id, res.content, insp.topic);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || '초안 생성에 실패했습니다.');
    } finally {
      setIsDirectSynthesizing(false);
    }
  };

  // -------------------------------------------------------------
  // Step 1: Search Seeds
  // -------------------------------------------------------------
  const handleSearchSeeds = async () => {
    if (!topic.trim()) {
      setErrorMsg('타깃 주제를 입력해주세요.');
      return;
    }
    setErrorMsg('');
    setLoading('isSearchingSeeds', true);

    try {
      const res = await draftApi.searchSeeds(topic, direction, 10);
      setCandidates(res.candidates);

      // Auto-select top recommended seeds
      const recommended = res.candidates.filter((c) => c.assigned_role).map((c) => c.doc_id);
      if (recommended.length > 0) {
        setSelectedSeedIds(recommended);
      } else if (res.candidates.length > 0) {
        setSelectedSeedIds(res.candidates.slice(0, 2).map((c) => c.doc_id));
      }

      setStep(2);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || '시드 검색 중 오류가 발생했습니다.');
    } finally {
      setLoading('isSearchingSeeds', false);
    }
  };

  // -------------------------------------------------------------
  // Step 2: Generate Blueprint
  // -------------------------------------------------------------
  const handleGenerateBlueprint = async () => {
    setErrorMsg('');
    setLoading('isGeneratingBlueprint', true);

    try {
      const res = await draftApi.generateBlueprint(
        topic,
        direction,
        targetArchetype,
        selectedSeedIds,
        step2Model
      );
      setBlueprint(res);
      setStep(3);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || '블루프린트 기획안 생성에 실패했습니다.');
    } finally {
      setLoading('isGeneratingBlueprint', false);
    }
  };

  // -------------------------------------------------------------
  // Step 3: Synthesize Final Draft
  // -------------------------------------------------------------
  const handleSynthesize = async () => {
    setErrorMsg('');
    setLoading('isSynthesizing', true);

    try {
      const res = await draftApi.synthesize(
        topic,
        direction,
        targetArchetype,
        selectedSeedIds,
        blueprint?.raw_blueprint || {},
        2500,
        step3Model
      );
      setDraftContent(res.content);
      if (res.creation_id) {
        setCreationId(res.creation_id);
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || '초안 생성에 실패했습니다.');
    } finally {
      setLoading('isSynthesizing', false);
    }
  };

  const handleOpenInEditor = () => {
    onOpenEditor(creationId || undefined, draftContent, topic);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Wizard Progress Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">AI 에세이 & 아티클 초안 생성기</h1>
            <p className="text-sm text-slate-500 mt-1">
              색인된 나만의 지식 자산(Seeds)에서 소재를 발굴하여 깊이 있는 초안을 완성합니다.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <ModelSelector
              value={inspirationModel}
              onChange={setInspirationModel}
              disabled={isLoadingInspiration || isDirectSynthesizing}
              labelPrefix="AI 모델:"
            />
            <button
              onClick={handleFetchRandomInspiration}
              disabled={isLoadingInspiration || isDirectSynthesizing}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-lg transition-all shadow-xs disabled:opacity-50"
              title="데이터베이스의 글들을 분석하여 새로운 주제와 초안을 자동 기획합니다"
            >
              {isLoadingInspiration ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-600" />
              ) : (
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              )}
              <span>{isLoadingInspiration ? '영감 발굴 중...' : '랜덤생성'}</span>
            </button>
            <button
              onClick={() => {
                if (window.confirm('입력한 내용을 모두 지우고 완전히 새로 시작하시겠습니까?')) {
                  resetDraft();
                }
              }}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 rounded-lg transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>새 글 초기화</span>
            </button>
          </div>
        </div>

        {/* Steps indicator */}
        <div className="grid grid-cols-3 gap-3">
          <div
            className={`p-3 rounded-xl border flex items-center space-x-3 transition-all ${
              step === 1
                ? 'bg-indigo-50/70 border-indigo-200 text-indigo-900 shadow-xs'
                : step > 1
                ? 'bg-slate-50 border-slate-200 text-slate-700'
                : 'bg-white border-slate-200 text-slate-400'
            }`}
          >
            <span
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                step === 1 ? 'bg-indigo-600 text-white' : step > 1 ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
              }`}
            >
              {step > 1 ? <Check className="w-4 h-4" /> : '1'}
            </span>
            <div className="text-left">
              <div className="text-xs font-bold leading-none">1단계: 타깃 생각 정의</div>
              <div className="text-[11px] text-slate-500 mt-0.5">주제와 고유 관점 입력</div>
            </div>
          </div>

          <div
            className={`p-3 rounded-xl border flex items-center space-x-3 transition-all ${
              step === 2
                ? 'bg-indigo-50/70 border-indigo-200 text-indigo-900 shadow-xs'
                : step > 2
                ? 'bg-slate-50 border-slate-200 text-slate-700'
                : 'bg-white border-slate-200 text-slate-400'
            }`}
          >
            <span
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                step === 2 ? 'bg-indigo-600 text-white' : step > 2 ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
              }`}
            >
              {step > 2 ? <Check className="w-4 h-4" /> : '2'}
            </span>
            <div className="text-left">
              <div className="text-xs font-bold leading-none">2단계: 소재(시드) 선택</div>
              <div className="text-[11px] text-slate-500 mt-0.5">상호보완적 지식 매칭</div>
            </div>
          </div>

          <div
            className={`p-3 rounded-xl border flex items-center space-x-3 transition-all ${
              step === 3
                ? 'bg-indigo-50/70 border-indigo-200 text-indigo-900 shadow-xs'
                : 'bg-white border-slate-200 text-slate-400'
            }`}
          >
            <span
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                step === 3 ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-600'
              }`}
            >
              3
            </span>
            <div className="text-left">
              <div className="text-xs font-bold leading-none">3단계: 기획안 & 초안</div>
              <div className="text-[11px] text-slate-500 mt-0.5">블루프린트 검토 및 완성</div>
            </div>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2 text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* ========================================================= */}
      {/* Step 1: Input Topic & Intent                              */}
      {/* ========================================================= */}
      {step === 1 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">
          {/* Random Idea Inspiration Banner */}
          <div className="p-4 bg-gradient-to-r from-indigo-50/90 via-purple-50/70 to-slate-50 border border-indigo-100 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start sm:items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs mt-0.5 sm:mt-0">
                <Dices className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <span>어떤 주제로 글을 쓸지 막막하신가요?</span>
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded-full">추천</span>
                </h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  데이터베이스의 지식 자산을 결합하여 새로운 주제와 집필 관점을 자동으로 도출해 드립니다.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleFetchRandomInspiration}
              disabled={isLoadingInspiration || isDirectSynthesizing}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs shrink-0 transition-all flex items-center justify-center space-x-1.5 disabled:opacity-50"
            >
              {isLoadingInspiration ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>{isLoadingInspiration ? '영감 찾는 중...' : '랜덤생성'}</span>
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm font-bold text-slate-900">
                1. 이번에 쓰고자 하는 타깃 주제 (Topic) <span className="text-rose-500">*</span>
              </label>
              {topic && (
                <button
                  type="button"
                  onClick={() => setTopic('')}
                  className="text-xs text-slate-400 hover:text-rose-600 transition-colors"
                >
                  지우기
                </button>
              )}
            </div>
            <p className="text-xs text-slate-500 mb-2">
              독자에게 던지고 싶은 핵심 질문이나 다루고자 하는 구체적인 업무/비즈니스 주제를 적어주세요.
            </p>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="작성할 주제나 핵심 화두를 입력하세요 (예: 지속 가능한 프로덕트 개발과 팀 빌딩)"
              className="w-full px-4 py-3 rounded-xl border border-slate-300 text-slate-900 placeholder:text-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm font-bold text-slate-900">
                2. 나만의 집필 방향 및 고유 관점 (Perspective / Direction)
              </label>
              {direction && (
                <button
                  type="button"
                  onClick={() => setDirection('')}
                  className="text-xs text-slate-400 hover:text-rose-600 transition-colors"
                >
                  지우기
                </button>
              )}
            </div>
            <p className="text-xs text-slate-500 mb-2">
              이 글에서 전개하고 싶은 나의 경험, 독창적인 주장이나 강조하고 싶은 결론을 자유롭게 메모해주세요. (미입력 시 AI가 기본 중립 모드로 집필)
            </p>
            <textarea
              rows={4}
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
              placeholder="글에 담고 싶은 나만의 고유한 경험, 주장, 결론을 메모하세요 (선택 사항)"
              className="w-full px-4 py-3 rounded-xl border border-slate-300 text-slate-900 placeholder:text-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 leading-relaxed"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-900 mb-2">3. 글의 타깃 아키타입 (스타일 구조)</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {ARCHETYPES.map((arch) => (
                <div
                  key={arch.id}
                  onClick={() => setTargetArchetype(arch.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    targetArchetype === arch.id
                      ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-500/20'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-sm text-slate-900">{arch.label}</span>
                    {targetArchetype === arch.id ? (
                      <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                    ) : (
                      <Circle className="w-4 h-4 text-slate-300" />
                    )}
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{arch.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              onClick={handleSearchSeeds}
              disabled={isSearchingSeeds || !topic.trim()}
              className="flex items-center space-x-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-sm rounded-xl transition-all shadow-sm"
            >
              <span>{isSearchingSeeds ? '색인 데이터 검색 중...' : '저장된 지식에서 소재 찾기'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* Step 2: Seed Selection                                    */}
      {/* ========================================================= */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-xs font-bold text-slate-500 uppercase">타깃 주제</span>
              <span className="text-sm font-bold text-slate-900">{topic}</span>
            </div>
            <button
              onClick={() => setStep(1)}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
            >
              주제 수정
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">검색된 시드 소재 (총 {candidates.length}건)</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                AI가 주제와의 상호보완성을 분석하여 추천한 지식 카드들입니다. 글에 녹여낼 소재를 선택해주세요.
              </p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-100">
              {selectedSeedIds.length}개 선택됨
            </span>
          </div>

          <div className="space-y-3">
            {candidates.map((cand) => {
              const isSelected = selectedSeedIds.includes(cand.doc_id);
              const roleBadge =
                cand.assigned_role === 'domain_case'
                  ? '🏆 핵심 사례/도메인'
                  : cand.assigned_role === 'perspective_framework'
                  ? '💡 관점 & 프레임워크'
                  : cand.assigned_role === 'synthesis_counterpoint'
                  ? '⚖️ 대조/보완 시드'
                  : null;

              return (
                <div
                  key={cand.doc_id}
                  onClick={() => toggleSeed(cand.doc_id)}
                  className={`p-5 rounded-2xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-indigo-600 bg-white shadow-xs ring-2 ring-indigo-500/20'
                      : 'border-slate-200 bg-white/70 hover:bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1 pr-3">
                      <div className="flex items-center space-x-2">
                        {roleBadge && (
                          <span className="text-xs font-bold px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded-md">
                            {roleBadge}
                          </span>
                        )}
                        <span className="text-xs font-semibold text-slate-400">#{cand.doc_id}</span>
                        <span className="text-xs font-medium text-slate-500">[{cand.archetype}]</span>
                      </div>
                      <h3 className="font-bold text-base text-slate-900 group-hover:text-indigo-600 transition-colors">
                        {cand.title}
                      </h3>
                    </div>

                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setViewingSeedDocId(cand.doc_id);
                        }}
                        className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 hover:border-indigo-300 rounded-xl transition-all shadow-2xs"
                        title="이 시드의 원문 전문 및 상세 메타데이터 열람"
                      >
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>원문 보기</span>
                      </button>

                      <div className="p-1" title={isSelected ? '소재 선택 해제' : '소재 선택'}>
                        {isSelected ? (
                          <CheckCircle2 className="w-5 h-5 text-indigo-600" />
                        ) : (
                          <Circle className="w-5 h-5 text-slate-300" />
                        )}
                      </div>
                    </div>
                  </div>

                  {cand.core_thesis && (
                    <p className="mt-2 text-xs text-slate-600 line-clamp-2 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <strong>핵심 테제:</strong> {cand.core_thesis}
                    </p>
                  )}

                  {cand.notable_episodes && cand.notable_episodes.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {cand.notable_episodes.slice(0, 2).map((ep, idx) => (
                        <span key={idx} className="text-[11px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
                          📌 {ep}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
            <button
              onClick={() => setStep(1)}
              className="flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>이전 단계</span>
            </button>

            <div className="flex items-center space-x-2">
              <ModelSelector
                value={step2Model}
                onChange={setStep2Model}
                disabled={isGeneratingBlueprint}
                labelPrefix="기획 모델:"
              />
              <button
                onClick={handleGenerateBlueprint}
                disabled={isGeneratingBlueprint || selectedSeedIds.length === 0}
                className="flex items-center space-x-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-sm rounded-xl transition-all shadow-sm"
              >
                <span>{isGeneratingBlueprint ? '기획안 설계 중...' : '기획안(블루프린트) 생성'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* Step 3: Blueprint & Synthesis                             */}
      {/* ========================================================= */}
      {step === 3 && (
        <div className="space-y-6">
          {/* Blueprint Card */}
          {blueprint && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center space-x-2 text-indigo-600">
                  <Layers className="w-5 h-5" />
                  <h3 className="font-bold text-slate-900 text-lg">기획 설계도 (Blueprint)</h3>
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-full">
                  타깃 독자: {blueprint.target_audience || '실무자'}
                </span>
              </div>

              <div>
                <span className="text-xs font-bold text-slate-400 block mb-0.5">가제 (Working Title)</span>
                <h2 className="text-xl font-extrabold text-slate-900">{blueprint.working_title}</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl text-xs">
                <div>
                  <span className="font-bold text-slate-700 block mb-1">🎯 핵심 테제 (Core Thesis)</span>
                  <p className="text-slate-600 leading-relaxed">{blueprint.core_thesis}</p>
                </div>
                <div>
                  <span className="font-bold text-slate-700 block mb-1">🪝 첫인상 후킹 전략 (Hook)</span>
                  <p className="text-slate-600 leading-relaxed">{blueprint.hook_strategy}</p>
                </div>
              </div>

              {blueprint.outline_sections && blueprint.outline_sections.length > 0 && (
                <div>
                  <span className="text-xs font-bold text-slate-700 block mb-2">📋 문단별 전개 목차</span>
                  <div className="space-y-2">
                    {blueprint.outline_sections.map((sec: any, idx: number) => (
                      <div key={idx} className="p-3 bg-white rounded-xl border border-slate-200 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-slate-900">
                            {idx + 1}. {sec.section_title || sec.title}
                          </span>
                          <span className="text-[11px] text-slate-400">목표: {sec.section_goal || ''}</span>
                        </div>
                        {sec.key_points && (
                          <p className="text-slate-600 text-[11px] leading-relaxed">
                            {Array.isArray(sec.key_points) ? sec.key_points.join(' • ') : sec.key_points}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Synthesis Trigger Button */}
          {!draftContent && (
            <div className="bg-indigo-600 rounded-2xl p-6 text-white flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-md">
              <div>
                <h4 className="font-bold text-lg">이제 완성도 높은 초안을 합성할 준비가 되었습니다.</h4>
                <p className="text-xs text-indigo-100 mt-1">
                  선택한 시드의 원문 맥락을 완전히 녹여내어 나만의 1인칭 관점과 독창적 프레임워크로 2,500자 원고를 작성합니다.
                </p>
              </div>
              <div className="flex items-center space-x-2 shrink-0">
                <ModelSelector
                  value={step3Model}
                  onChange={setStep3Model}
                  disabled={isSynthesizing}
                  className="bg-indigo-700/80 border-indigo-400 text-white"
                  labelPrefix="합성 모델:"
                />
                <button
                  onClick={handleSynthesize}
                  disabled={isSynthesizing}
                  className="px-6 py-3 bg-white text-indigo-700 hover:bg-indigo-50 font-extrabold text-sm rounded-xl transition-all shadow-sm shrink-0"
                >
                  {isSynthesizing ? '원고 집필 합성 중...' : '🚀 초안 생성 시작'}
                </button>
              </div>
            </div>
          )}

          {/* Generated Draft Display */}
          {draftContent && (
            <div className="bg-white rounded-2xl border border-emerald-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-emerald-100 pb-3">
                <div className="flex items-center space-x-2 text-emerald-600">
                  <FileText className="w-5 h-5" />
                  <h3 className="font-bold text-slate-900 text-lg">초안 합성 완성</h3>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-full">
                    글자수: {draftContent.length.toLocaleString()}자
                  </span>
                  <ModelSelector
                    value={step3Model}
                    onChange={setStep3Model}
                    disabled={isSynthesizing}
                    labelPrefix="재합성 모델:"
                  />
                  <button
                    onClick={handleSynthesize}
                    disabled={isSynthesizing}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-colors"
                  >
                    <span>{isSynthesizing ? '합성 중...' : '다시 합성'}</span>
                  </button>
                  <button
                    onClick={handleOpenInEditor}
                    className="flex items-center space-x-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl transition-colors shadow-xs"
                  >
                    <Edit className="w-3.5 h-3.5" />
                    <span>스튜디오 에디터에서 퇴고하기 →</span>
                  </button>
                </div>
              </div>

              <div className="max-h-[500px] overflow-y-auto p-4 bg-slate-50 rounded-xl text-sm text-slate-800 font-mono whitespace-pre-wrap leading-relaxed border border-slate-200">
                {draftContent}
              </div>
            </div>
          )}

          {/* Visual Seed Assets Gallery Section */}
          {visualAssets && visualAssets.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center space-x-2 text-indigo-600">
                  <ImageIcon className="w-5 h-5" />
                  <h3 className="font-bold text-slate-900 text-base">
                    인용된 Seed 시각 자료 및 이미지 ({visualAssets.length}건)
                  </h3>
                </div>
                <span className="text-xs text-slate-400">클릭하여 확대 및 본문 삽입 제안 확인</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {visualAssets.map((asset, idx) => (
                  <div
                    key={`${asset.doc_id}_${asset.asset_id}_${idx}`}
                    onClick={() => setSelectedLightboxAsset(asset)}
                    className="group border border-slate-200 rounded-xl overflow-hidden hover:border-indigo-400 hover:shadow-xs transition-all cursor-pointer bg-slate-50 flex flex-col"
                  >
                    <div className="relative aspect-4/3 overflow-hidden bg-slate-200">
                      <img
                        src={asset.image_url}
                        alt={asset.caption || asset.asset_id}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                        loading="lazy"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                      <div className="absolute inset-0 bg-slate-900/0 group-hover:bg-slate-900/30 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <ZoomIn className="w-5 h-5 text-white" />
                      </div>
                      <span className="absolute top-1.5 left-1.5 text-[10px] font-bold bg-slate-900/75 text-white px-1.5 py-0.5 rounded">
                        p.{asset.page_no}
                      </span>
                    </div>
                    <div className="p-2.5 flex-1 flex flex-col justify-between">
                      <div className="text-[11px] font-bold text-slate-800 line-clamp-1" title={asset.doc_title}>
                        {asset.doc_title}
                      </div>
                      <p className="text-[10px] text-slate-500 line-clamp-2 mt-0.5">
                        {asset.caption || asset.asset_id}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}


          <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
            <button
              onClick={() => setStep(2)}
              className="flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>소재 선택으로 돌아가기</span>
            </button>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* Random Inspiration Modal                                  */}
      {/* ========================================================= */}
      {showInspirationModal && inspiration && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-indigo-100 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-xs">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">AI 추천 집필 영감 & 지식 조합</h3>
                  <p className="text-xs text-slate-500">데이터베이스의 상호보완적 시드를 크로스 융합했습니다.</p>
                </div>
              </div>
              <button
                onClick={() => setShowInspirationModal(false)}
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-white rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-5 text-left">
              {/* Concept Summary Badge */}
              {inspiration.concept_summary && (
                <div className="p-3 bg-indigo-50/50 border border-indigo-100 rounded-xl text-xs text-indigo-900 font-medium leading-relaxed">
                  💡 <span className="font-bold">기획 의도:</span> {inspiration.concept_summary}
                </div>
              )}

              {/* Topic */}
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  1. 추천 타깃 주제 (Topic)
                </span>
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-slate-900 font-extrabold text-base leading-snug">
                  {inspiration.topic}
                </div>
              </div>

              {/* Direction */}
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  2. 추천 집필 방향 & 고유 관점
                </span>
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 leading-relaxed font-medium">
                  {inspiration.direction}
                </div>
              </div>

              {/* Archetype */}
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  3. 추천 스타일 아키타입
                </span>
                <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100 border border-slate-200 rounded-lg text-xs font-bold text-slate-800">
                  <span>
                    {ARCHETYPES.find((a) => a.id === inspiration.target_archetype)?.label ||
                      inspiration.target_archetype}
                  </span>
                </div>
              </div>

              {/* Selected DB Seeds */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
                    <span>4. 결합된 원천 DB 지식 자산 ({inspiration.selected_seeds.length}편)</span>
                  </span>
                  <span className="text-[11px] text-slate-500 font-medium">상호보완적 다중 시드 융합</span>
                </div>
                <div className="space-y-2">
                  {inspiration.selected_seeds.map((s, idx) => (
                    <div
                      key={s.doc_id}
                      className="p-3 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-colors text-left"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-slate-900 truncate pr-2">
                          {s.title}
                        </span>
                        <div className="flex items-center space-x-1.5 shrink-0">
                          <button
                            type="button"
                            onClick={() => setViewingSeedDocId(s.doc_id)}
                            className="flex items-center space-x-1 text-[11px] font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 px-2 py-0.5 rounded-md transition-colors"
                            title="원문 전문 및 상세 정보 열람"
                          >
                            <BookOpen className="w-3 h-3" />
                            <span>원문</span>
                          </button>
                          <span className="text-[10px] font-semibold px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md">
                            {idx === 0
                              ? '사례/문제'
                              : idx === 1
                              ? '관점 전환'
                              : '실행 도구'}
                          </span>
                        </div>
                      </div>
                      {s.core_thesis && (
                        <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                          {s.core_thesis}
                        </p>
                      )}
                      {s.topic_tags && s.topic_tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {s.topic_tags.slice(0, 4).map((tag, tIdx) => (
                            <span
                              key={tIdx}
                              className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
              <button
                type="button"
                onClick={handleFetchRandomInspiration}
                disabled={isLoadingInspiration || isDirectSynthesizing}
                className="w-full sm:w-auto flex items-center justify-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-300 hover:bg-slate-50 rounded-xl transition-colors disabled:opacity-50"
              >
                {isLoadingInspiration ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Dices className="w-3.5 h-3.5" />
                )}
                <span>다른 조합 뽑기</span>
              </button>

              <div className="w-full sm:w-auto flex flex-wrap items-center justify-end gap-2">
                <ModelSelector
                  value={inspirationModel}
                  onChange={setInspirationModel}
                  disabled={isDirectSynthesizing}
                  labelPrefix="작성 모델:"
                />
                <button
                  type="button"
                  onClick={() => handleApplyToForm(inspiration)}
                  disabled={isDirectSynthesizing}
                  className="flex-1 sm:flex-initial flex items-center justify-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white border border-slate-300 hover:bg-slate-50 rounded-xl transition-colors"
                >
                  <Edit className="w-3.5 h-3.5" />
                  <span>내용을 폼에 채우기</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDirectSynthesize(inspiration)}
                  disabled={isDirectSynthesizing}
                  className="flex-1 sm:flex-initial flex items-center justify-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs transition-colors disabled:opacity-50"
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>이 조합으로 바로 초안 작성 🚀</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* Lightbox Modal for Seed Visual Assets                     */}
      {/* ========================================================= */}
      {selectedLightboxAsset && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <ImageIcon className="w-4 h-4 text-indigo-600" />
                <h4 className="text-xs font-bold text-slate-800 truncate max-w-[450px]">
                  {selectedLightboxAsset.doc_title} (p.{selectedLightboxAsset.page_no})
                </h4>
              </div>
              <button
                onClick={() => setSelectedLightboxAsset(null)}
                className="p-1 text-slate-400 hover:text-slate-700 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[60vh] flex items-center justify-center bg-slate-100">
              <img
                src={selectedLightboxAsset.image_url}
                alt={selectedLightboxAsset.caption}
                className="max-w-full max-h-[55vh] object-contain rounded-lg shadow-sm"
              />
            </div>
            <div className="p-4 bg-white border-t border-slate-200 space-y-2">
              {selectedLightboxAsset.caption && (
                <p className="text-xs text-slate-700 font-medium">
                  <strong>원문 캡션:</strong> {selectedLightboxAsset.caption}
                </p>
              )}
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-center justify-between gap-2">
                <code className="text-[11px] text-indigo-700 font-mono truncate">
                  {`> 🖼️ **[시각 자료 제안 | Seed #${selectedLightboxAsset.doc_id} - ${selectedLightboxAsset.asset_id}]**: ${selectedLightboxAsset.caption || selectedLightboxAsset.doc_title}`}
                </code>
                <button
                  onClick={() => {
                    const text = `> 🖼️ **[시각 자료 제안 | Seed #${selectedLightboxAsset.doc_id} - ${selectedLightboxAsset.asset_id}]**: ${selectedLightboxAsset.caption || selectedLightboxAsset.doc_title}`;
                    navigator.clipboard.writeText(text);
                    alert('본문 삽입용 코드가 클립보드에 복사되었습니다.');
                  }}
                  className="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 text-[11px] font-bold rounded shadow-2xs transition-colors shrink-0"
                >
                  코드 복사
                </button>
              </div>
            </div>
          </div>
        </div>
      )}


      {/* ========================================================= */}
      {/* Direct Synthesize Loading Overlay                         */}
      {/* ========================================================= */}
      {isDirectSynthesizing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl border border-slate-200 text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center mx-auto shadow-xs">
              <Loader2 className="w-7 h-7 animate-spin" />
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-lg">AI 초안 자동 작성 중...</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                DB 시드 3편의 핵심 논지와 프레임워크를 결합하여<br />
                약 2,500자 분량의 완성형 에세이 초안을 집필하고 있습니다.
              </p>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
              <div className="bg-indigo-600 h-full rounded-full animate-pulse w-3/4" />
            </div>
            <p className="text-[11px] text-slate-400">완료되면 스튜디오 에디터로 자동 전환됩니다.</p>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* Seed Original Full Text & Detail Modal                     */}
      {/* ========================================================= */}
      <SeedDetailModal
        docId={viewingSeedDocId}
        isOpen={Boolean(viewingSeedDocId)}
        onClose={() => setViewingSeedDocId(null)}
        isSelected={viewingSeedDocId ? selectedSeedIds.includes(viewingSeedDocId) : false}
        onToggleSelect={toggleSeed}
      />
    </div>
  );
};
