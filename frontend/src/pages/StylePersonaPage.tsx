import { useState, useEffect } from 'react';
import { Sparkles, Brain, CheckCircle2, BookOpen } from 'lucide-react';
import { styleApi, editorApi } from '../api/client';
import type { StyleProfileResponse } from '../api/client';

export const StylePersonaPage = () => {
  const [profile, setProfile] = useState<StyleProfileResponse | null>(null);
  const [isLearning, setIsLearning] = useState(false);
  const [learnMessage, setLearnMessage] = useState('');
  const [finalizedCount, setFinalizedCount] = useState(0);

  const loadData = async () => {
    try {
      const [res, creations] = await Promise.all([
        styleApi.getStyle(),
        editorApi.listCreations('FINALIZED'),
      ]);
      setProfile(res);
      setFinalizedCount(creations.length);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleLearnStyle = async () => {
    setIsLearning(true);
    setLearnMessage('');
    try {
      const res = await styleApi.learnStyle(Math.min(3, Math.max(1, finalizedCount)));
      setLearnMessage(res.message);
      if (res.success) {
        await loadData();
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || '스타일 학습 중 오류가 발생했습니다.');
    } finally {
      setIsLearning(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Intro Banner */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-xs flex items-start space-x-4">
        <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 text-amber-400">
          <Brain className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h2 className="font-bold text-base">페르소나 문체 학습실 (Style Learning Lab)</h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            퇴고가 완료된 글(FINALIZED)과 AI 초안의 차이(Diff)를 분석하여 글쓴이 고유의 어투, 사고 프레임워크, 즐겨 쓰는 문장 전개 방식을 학습합니다. 누적 퇴고작이 쌓일수록 초안 생성이 글쓴이의 목소리를 더욱 정밀하게 모사합니다.
          </p>
        </div>
      </div>

      {learnMessage && (
        <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center space-x-2 text-xs font-bold text-indigo-900">
          <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0" />
          <span>{learnMessage}</span>
        </div>
      )}

      {/* Main Profile Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Active Persona</span>
              <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md flex items-center space-x-1">
                <BookOpen className="w-3 h-3 text-slate-500" />
                <span>퇴고 완료작 {finalizedCount}편 보유</span>
              </span>
            </div>
            <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">
              {profile?.persona_name || 'Chief Business Essayist'}
            </h1>
          </div>
          <button
            onClick={handleLearnStyle}
            disabled={isLearning || finalizedCount === 0}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition-all shadow-xs flex items-center space-x-1.5"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isLearning ? '퇴고작 분석 및 문체 학습 중...' : `🧬 퇴고작 기반 문체 학습 (${finalizedCount}편)`}</span>
          </button>
        </div>

        {/* Tone & Manner */}
        <div>
          <h3 className="text-xs font-bold text-slate-700 mb-2">🎭 핵심 어조 및 태도 (Tone & Manner)</h3>
          <div className="space-y-1.5">
            {profile?.tone_and_manner?.map((item, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <span className="text-indigo-600 font-bold">•</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Sentence Style & Mechanics */}
        <div>
          <h3 className="text-xs font-bold text-slate-700 mb-2">📏 문장 호흡 및 문단 구조</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="font-semibold text-slate-500 block mb-1">선호 어미</span>
              <span className="font-bold text-slate-800">
                {profile?.sentence_style?.preferred_ending || '합니다/하십시오'}
              </span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="font-semibold text-slate-500 block mb-1">문단 전개 공식</span>
              <span className="font-bold text-slate-800">
                {profile?.sentence_style?.paragraph_structure || '도입 훅 -> 반전 -> 실행 프레임워크'}
              </span>
            </div>
          </div>
        </div>

        {/* Storytelling structures */}
        <div>
          <h3 className="text-xs font-bold text-slate-700 mb-2">📖 스토리텔링 전개 패턴</h3>
          <div className="space-y-1.5">
            {profile?.storytelling_structures?.map((item, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <span className="text-emerald-600 font-bold">✓</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Banned patterns */}
        {profile?.banned_patterns && profile.banned_patterns.length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-rose-700 mb-2">🚫 금지된 상투적 클리셰 (Banned Patterns)</h3>
            <div className="space-y-1.5">
              {profile.banned_patterns.map((item, idx) => (
                <div key={idx} className="flex items-start space-x-2 text-xs text-rose-800 bg-rose-50 p-2.5 rounded-lg border border-rose-100">
                  <span className="font-bold">✕</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
