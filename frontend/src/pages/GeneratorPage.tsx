import { useState } from 'react';
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
} from 'lucide-react';
import { draftApi } from '../api/client';
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
    resetDraft,
  } = useDraftStore();

  const [errorMsg, setErrorMsg] = useState('');

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
      const res = await draftApi.generateBlueprint(topic, direction, targetArchetype, selectedSeedIds);
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
        2500
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
          <div>
            <label className="block text-sm font-bold text-slate-900 mb-1.5">
              1. 이번에 쓰고자 하는 타깃 주제 (Topic) <span className="text-rose-500">*</span>
            </label>
            <p className="text-xs text-slate-500 mb-2">
              독자에게 던지고 싶은 핵심 질문이나 다루고자 하는 구체적인 업무/비즈니스 주제를 적어주세요.
            </p>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="예: AI 코딩 시대, 기획자의 진짜 존재 이유와 오버엔지니어링 방지법"
              className="w-full px-4 py-3 rounded-xl border border-slate-300 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-900 mb-1.5">
              2. 나만의 집필 방향 및 고유 관점 (Perspective / Direction)
            </label>
            <p className="text-xs text-slate-500 mb-2">
              이 글에서 전개하고 싶은 나의 경험, 독창적인 주장이나 강조하고 싶은 결론을 자유롭게 메모해주세요.
            </p>
            <textarea
              rows={4}
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
              placeholder="예: 코딩은 AI가 너무 잘하지만 목적과 방향, 비용 제약은 여전히 기획자가 설정해야 한다. 소규모 친목 모임에 월 50만원 쿠버네티스를 붙여버리는 AI의 맹점을 짚고 진짜 기획자의 3대 점검 기준을 제시한다."
              className="w-full px-4 py-3 rounded-xl border border-slate-300 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 leading-relaxed"
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
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        {roleBadge && (
                          <span className="text-xs font-bold px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded-md">
                            {roleBadge}
                          </span>
                        )}
                        <span className="text-xs font-semibold text-slate-400">#{cand.doc_id}</span>
                        <span className="text-xs font-medium text-slate-500">[{cand.archetype}]</span>
                      </div>
                      <h3 className="font-bold text-base text-slate-900">{cand.title}</h3>
                    </div>

                    <div className="p-1">
                      {isSelected ? (
                        <CheckCircle2 className="w-5 h-5 text-indigo-600" />
                      ) : (
                        <Circle className="w-5 h-5 text-slate-300" />
                      )}
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
            <div className="bg-indigo-600 rounded-2xl p-6 text-white flex items-center justify-between shadow-md">
              <div>
                <h4 className="font-bold text-lg">이제 완성도 높은 초안을 합성할 준비가 되었습니다.</h4>
                <p className="text-xs text-indigo-100 mt-1">
                  선택한 시드의 원문 맥락을 분리(De-contextualize)하여 나만의 순수 관점으로 원고를 작성합니다.
                </p>
              </div>
              <button
                onClick={handleSynthesize}
                disabled={isSynthesizing}
                className="px-6 py-3 bg-white text-indigo-700 hover:bg-indigo-50 font-extrabold text-sm rounded-xl transition-all shadow-sm shrink-0"
              >
                {isSynthesizing ? '원고 집필 합성 중...' : '🚀 초안 생성 시작'}
              </button>
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
    </div>
  );
};
