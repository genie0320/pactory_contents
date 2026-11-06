import { useState, useEffect } from 'react';
import {
  Save,
  Sparkles,
  Copy,
  Check,
  CheckCircle,
} from 'lucide-react';
import { editorApi } from '../api/client';
import type { ProofreadResponse } from '../api/client';

interface StudioEditorPageProps {
  initialCreationId?: string;
  initialDraftContent?: string;
  initialTopic?: string;
}

export const StudioEditorPage = ({
  initialCreationId,
  initialDraftContent = '',
  initialTopic = '',
}: StudioEditorPageProps) => {
  const [creationId, setCreationId] = useState(initialCreationId || '');
  const [topic, setTopic] = useState(initialTopic);
  const [content, setContent] = useState(initialDraftContent);
  const [customNotes, setCustomNotes] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Proofreader state
  const [platform, setPlatform] = useState('general');
  const [proofMode, setProofMode] = useState<'report' | 'rewrite'>('report');
  const [customInstruction, setCustomInstruction] = useState('');
  const [isProofreading, setIsProofreading] = useState(false);
  const [proofResult, setProofResult] = useState<ProofreadResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // If creationId is passed, load existing content
  useEffect(() => {
    if (initialCreationId) {
      editorApi.getCreation(initialCreationId).then((res) => {
        setTopic(res.topic);
        setContent(res.user_final_text || res.ai_draft_text);
        setCustomNotes(res.custom_notes || '');
      });
    }
  }, [initialCreationId]);

  const handleSave = async (status = 'FINALIZED') => {
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      if (creationId) {
        await editorApi.updateCreation(creationId, {
          user_final_text: content,
          custom_notes: customNotes,
          status,
        });
      } else {
        const saved = await editorApi.saveCreation({
          topic: topic || '새로운 아티클',
          ai_draft_text: content,
          user_final_text: content,
          status,
        });
        setCreationId(saved.creation_id);
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert('저장에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleProofread = async () => {
    if (!content.trim()) {
      alert('분석할 본문 내용이 없습니다.');
      return;
    }
    setIsProofreading(true);
    try {
      const res = await editorApi.proofread({
        content,
        platform,
        mode: proofMode,
        custom_instruction: customInstruction,
        critique_feedback: '',
      });
      setProofResult(res);
    } catch (err: any) {
      alert(err.response?.data?.detail || '에디토리얼 첨삭 호출 중 오류가 발생했습니다.');
    } finally {
      setIsProofreading(false);
    }
  };

  const handleApplyRewrite = () => {
    if (proofResult?.rewritten_text) {
      if (window.confirm('AI 개정본 내용으로 에디터 본문을 덮어쓰시겠습니까?')) {
        setContent(proofResult.rewritten_text);
      }
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Top action header */}
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
        <div>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Studio Editor & Proofreader</span>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
            {topic || '제목 미정의 원고'}
          </h1>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? '복사됨!' : '본문 복사'}</span>
          </button>

          <button
            onClick={() => handleSave('FINALIZED')}
            disabled={isSaving}
            className="flex items-center space-x-1 px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg transition-colors shadow-xs"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{isSaving ? '저장 중...' : '최종본 확정 저장'}</span>
          </button>
        </div>
      </div>

      {saveSuccess && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-xs font-bold text-emerald-800">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <span>성공적으로 저장되었습니다. 퇴고 완료된 글은 페르소나 스타일 학습에 사용될 수 있습니다.</span>
        </div>
      )}

      {/* Main split grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Content Editor */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col min-h-[650px]">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-600">원고 본문 (Markdown)</span>
            <span className="text-xs text-slate-400 font-mono">
              글자수: {content.length.toLocaleString()}자
            </span>
          </div>

          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="이곳에 원고를 작성하거나 AI 생성 초안을 다듬으세요..."
            className="w-full flex-1 p-3 text-sm font-mono leading-relaxed text-slate-800 border-none resize-none focus:outline-none"
          />

          <div className="pt-3 border-t border-slate-100">
            <input
              type="text"
              value={customNotes}
              onChange={(e) => setCustomNotes(e.target.value)}
              placeholder="퇴고 메모 (선택사항, 예: 후킹을 강화하고 3단계 공식을 강조함)"
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Right: Multi-Platform Editorial Copilot */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2 text-indigo-600">
                <Sparkles className="w-5 h-5" />
                <h3 className="font-bold text-slate-900 text-base">에디토리얼 코파일럿</h3>
              </div>
              <span className="text-xs font-bold text-slate-400">Multi-Platform</span>
            </div>

            {/* Platform selection pills */}
            <div>
              <span className="text-xs font-bold text-slate-700 block mb-1.5">1. 매체 타깃 선택</span>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'brunch', label: '☕ 브런치스토리' },
                  { id: 'linkedin', label: '💼 링크드인' },
                  { id: 'threads', label: '📱 스레드' },
                  { id: 'general', label: '🎯 종합 밸런스' },
                ].map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setPlatform(p.id)}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all ${
                      platform === p.id
                        ? 'bg-indigo-50 border-indigo-300 text-indigo-700 shadow-xs'
                        : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Mode selection pills */}
            <div>
              <span className="text-xs font-bold text-slate-700 block mb-1.5">2. 첨삭 모드</span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setProofMode('report')}
                  className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all ${
                    proofMode === 'report'
                      ? 'bg-slate-800 text-white border-slate-800 shadow-xs'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  📊 종합 진단 리포트
                </button>
                <button
                  onClick={() => setProofMode('rewrite')}
                  className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all ${
                    proofMode === 'rewrite'
                      ? 'bg-slate-800 text-white border-slate-800 shadow-xs'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  ✨ 매체 맞춤 개정본
                </button>
              </div>
            </div>

            {/* Custom instruction / refinement */}
            <div>
              <span className="text-xs font-bold text-slate-700 block mb-1.5">3. 추가 피드백 (선택)</span>
              <input
                type="text"
                value={customInstruction}
                onChange={(e) => setCustomInstruction(e.target.value)}
                placeholder="예: 도입부 후킹을 더 극적으로 하고, 체크리스트를 보강해줘"
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <button
              onClick={handleProofread}
              disabled={isProofreading || !content.trim()}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-extrabold rounded-xl transition-all shadow-xs flex items-center justify-center space-x-1.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isProofreading ? 'LLM 첨삭 분석 중...' : '매체 맞춤 첨삭 / 개정본 요청'}</span>
            </button>
          </div>

          {/* Results card */}
          {proofResult && (
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
              {/* Scores bar */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="text-[11px] text-slate-500">후킹 파워</div>
                  <div className="text-base font-extrabold text-indigo-600 mt-0.5">
                    {proofResult.hooking_score} / 10
                  </div>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="text-[11px] text-slate-500">전개 균형</div>
                  <div className="text-base font-extrabold text-indigo-600 mt-0.5">
                    {proofResult.balance_score} / 10
                  </div>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="text-[11px] text-slate-500">매체 정합도</div>
                  <div className="text-base font-extrabold text-indigo-600 mt-0.5">
                    {proofResult.platform_score} / 10
                  </div>
                </div>
              </div>

              {/* Critique report or rewrite content */}
              {proofResult.mode === 'rewrite' && proofResult.rewritten_text ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">✨ 매체 맞춤 개정본</span>
                    <button
                      onClick={handleApplyRewrite}
                      className="px-2.5 py-1 text-xs font-bold text-indigo-600 hover:bg-indigo-50 border border-indigo-200 rounded-lg transition-colors"
                    >
                      본문으로 채택하기
                    </button>
                  </div>
                  <div className="max-h-[350px] overflow-y-auto p-3 bg-slate-50 rounded-xl text-xs font-mono text-slate-800 whitespace-pre-wrap leading-relaxed border border-slate-200">
                    {proofResult.rewritten_text}
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-800">📊 종합 진단 리포트</span>
                  <div className="max-h-[350px] overflow-y-auto p-3 bg-slate-50 rounded-xl text-xs text-slate-800 whitespace-pre-wrap leading-relaxed border border-slate-200">
                    {proofResult.critique_report}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
