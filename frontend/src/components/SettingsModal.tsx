import React, { useEffect, useState } from 'react';
import {
  Settings,
  X,
  Cpu,
  Zap,
  CheckCircle2,
  AlertCircle,
  Activity,
  Save,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import {
  settingsApi,
  type SettingsResponse,
  type ModelInfoItem,
  type ModelTestResponse,
} from '../api/client';
import { useDraftStore } from '../store/useDraftStore';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const updateDefaultModel = useDraftStore((s) => s.updateDefaultModel);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Settings form states
  const [currentSettings, setCurrentSettings] = useState<SettingsResponse | null>(null);
  const [selectedModel, setSelectedModel] = useState('gemini-3-flash-preview');
  const [selectedProvider, setSelectedProvider] = useState('gemini');
  const [thinkingLevel, setThinkingLevel] = useState('low');
  const [geminiKey, setGeminiKey] = useState('');
  const [showKeyInput, setShowKeyInput] = useState(false);

  // Model test state
  const [testResult, setTestResult] = useState<ModelTestResponse | null>(null);

  useEffect(() => {
    if (isOpen) {
      setErrorMessage('');
      setSaveSuccess(false);
      setTestResult(null);
      setLoading(true);
      settingsApi
        .getSettings()
        .then((res) => {
          setCurrentSettings(res);
          setSelectedModel(res.default_model);
          setSelectedProvider(res.default_provider);
          setThinkingLevel(res.default_thinking_level || 'low');
        })
        .catch((err) => {
          setErrorMessage(err.response?.data?.detail || '설정을 불러오지 못했습니다.');
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleTestModel = async () => {
    setTesting(true);
    setTestResult(null);
    setErrorMessage('');
    try {
      const res = await settingsApi.testModel(selectedModel, selectedProvider);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        success: false,
        model: selectedModel,
        latency_ms: 0,
        message: err.response?.data?.detail || err.message || '테스트 요청 실패',
        error_type: 'REQUEST_FAILED',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMessage('');
    setSaveSuccess(false);

    try {
      const payload: any = {
        default_model: selectedModel,
        default_provider: selectedProvider,
        default_thinking_level: thinkingLevel,
      };
      if (geminiKey.trim()) {
        payload.gemini_api_key = geminiKey.trim();
      }

      const updated = await settingsApi.updateSettings(payload);
      setCurrentSettings(updated);
      updateDefaultModel(selectedModel);
      setSaveSuccess(true);
      setGeminiKey('');
      setShowKeyInput(false);

      setTimeout(() => {
        setSaveSuccess(false);
      }, 4000);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || '설정 저장 중 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const selectedModelMeta = currentSettings?.available_models.find((m) => m.id === selectedModel);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 overflow-y-auto"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100 transition-all max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 shrink-0">
          <div className="flex items-center space-x-2.5 text-indigo-600">
            <div className="p-2 bg-indigo-50 rounded-xl">
              <Settings className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h3 id="settings-modal-title" className="font-bold text-slate-900 text-lg">
                Pactory Studio 시스템 설정
              </h3>
              <p className="text-xs text-slate-500">
                기본 AI 모델 및 서비스 파라미터를 서버 무중단으로 실시간 변경합니다.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-16 space-y-3">
            <RefreshCw className="w-6 h-6 text-indigo-600 animate-spin" />
            <p className="text-xs font-medium text-slate-500">서버 설정 정보를 불러오는 중...</p>
          </div>
        ) : (
          <form onSubmit={handleSave} className="flex-1 overflow-y-auto py-4 space-y-5 pr-1">
            {errorMessage && (
              <div className="flex items-center space-x-2 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {saveSuccess && (
              <div className="flex items-center space-x-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-medium animate-fadeIn">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>설정이 성공적으로 저장되었습니다! 서버 재시작 없이 즉시 활성화됩니다.</span>
              </div>
            )}

            {/* Section 1: AI Model Selection & Test */}
            <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/80 space-y-3">
              <div className="flex items-center justify-between">
                <label className="flex items-center space-x-1.5 text-xs font-bold text-slate-800">
                  <Cpu className="w-4 h-4 text-indigo-600" />
                  <span>스튜디오 기본 AI 모델 (Default Model)</span>
                </label>
                <span className="text-[11px] text-slate-500 font-mono">
                  현재 활성: <strong className="text-slate-800">{currentSettings?.default_model}</strong>
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <select
                    value={selectedModel}
                    onChange={(e) => {
                      setSelectedModel(e.target.value);
                      const m = currentSettings?.available_models.find((item) => item.id === e.target.value);
                      if (m) setSelectedProvider(m.provider);
                      setTestResult(null);
                    }}
                    className="flex-1 px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-2xs"
                  >
                    {currentSettings?.available_models.map((m: ModelInfoItem) => (
                      <option key={m.id} value={m.id}>
                        {m.name} [{m.badge}] - {m.provider.toUpperCase()}
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    onClick={handleTestModel}
                    disabled={testing}
                    className="flex items-center space-x-1.5 px-3 py-2.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-xl text-xs font-bold transition-colors shrink-0 disabled:opacity-50"
                  >
                    {testing ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Activity className="w-3.5 h-3.5 text-indigo-600" />
                    )}
                    <span>{testing ? '핑 확인 중...' : '상태 핑 테스트'}</span>
                  </button>
                </div>

                {selectedModelMeta && (
                  <p className="text-[11px] text-slate-500 px-1">
                    {selectedModelMeta.description}
                  </p>
                )}

                {/* Model Test Result Banner */}
                {testResult && (
                  <div
                    className={`p-3 rounded-xl border text-xs flex items-start space-x-2 ${
                      testResult.success
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                        : testResult.error_type === 'RESOURCE_EXHAUSTED'
                        ? 'bg-amber-50 border-amber-300 text-amber-900'
                        : 'bg-rose-50 border-rose-200 text-rose-800'
                    }`}
                  >
                    {testResult.success ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <div className="font-bold flex items-center justify-between">
                        <span>
                          [{testResult.model}] {testResult.success ? '통신 성공' : '연결 또는 쿼터 경고'}
                        </span>
                        {testResult.latency_ms > 0 && (
                          <span className="font-mono text-[10px] opacity-80">
                            {testResult.latency_ms}ms
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 text-[11px] leading-relaxed opacity-90">
                        {testResult.message}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Section 2: Thinking Level (Reasoning Effort) */}
            <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/80 space-y-2.5">
              <label className="flex items-center space-x-1.5 text-xs font-bold text-slate-800">
                <Zap className="w-4 h-4 text-indigo-600" />
                <span>심층 추론 강도 (Thinking Level)</span>
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'low', label: 'Low (빠른 합성)', desc: '기본 권장, 지연시간 최소화' },
                  { id: 'medium', label: 'Medium (균형)', desc: '논리적 구체성 및 디테일 강화' },
                  { id: 'high', label: 'High (심층 사고)', desc: '장문 합성 및 복합 논거 정밀화' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setThinkingLevel(item.id)}
                    className={`p-2.5 text-left rounded-xl border text-xs transition-all ${
                      thinkingLevel === item.id
                        ? 'bg-white border-indigo-600 text-indigo-900 shadow-2xs ring-1 ring-indigo-500'
                        : 'bg-white/60 border-slate-200 text-slate-700 hover:bg-white'
                    }`}
                  >
                    <div className="font-bold">{item.label}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">{item.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Section 3: Observability & API Health Status */}
            <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/80 space-y-3">
              <div className="flex items-center justify-between">
                <label className="flex items-center space-x-1.5 text-xs font-bold text-slate-800">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>연결된 서비스 및 관측성(Observability) 상태</span>
                </label>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {/* Gemini Status */}
                <div className="flex items-center justify-between p-2.5 bg-white rounded-lg border border-slate-200">
                  <span className="font-medium text-slate-700">Google Gemini API</span>
                  {currentSettings?.api_keys_configured.gemini ? (
                    <span className="inline-flex items-center space-x-1 text-emerald-700 font-semibold text-[11px]">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span>정상 활성</span>
                    </span>
                  ) : (
                    <span className="text-rose-600 font-semibold text-[11px]">미설정</span>
                  )}
                </div>

                {/* Langfuse Status */}
                <div className="flex items-center justify-between p-2.5 bg-white rounded-lg border border-slate-200">
                  <span className="font-medium text-slate-700">Langfuse 모니터링</span>
                  {currentSettings?.langfuse_configured ? (
                    <span className="inline-flex items-center space-x-1 text-emerald-700 font-semibold text-[11px]">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      <span>연결됨 (Japan Cloud)</span>
                    </span>
                  ) : (
                    <span className="text-slate-400 font-semibold text-[11px]">미연결</span>
                  )}
                </div>
              </div>

              {/* Optional Key Update Accordion */}
              <div className="pt-1">
                <button
                  type="button"
                  onClick={() => setShowKeyInput(!showKeyInput)}
                  className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
                >
                  <span>{showKeyInput ? '▼ API 키 변경 접기' : '▶ 새 Gemini API 키 등록/교체하기'}</span>
                </button>

                {showKeyInput && (
                  <div className="mt-2 space-y-1.5 animate-fadeIn">
                    <input
                      type="password"
                      value={geminiKey}
                      onChange={(e) => setGeminiKey(e.target.value)}
                      placeholder="새로운 GEMINI_API_KEY 입력 (비워두면 기존 키 유지)"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-[10px] text-slate-500">
                      입력 시 서버의 .env에 저장되며 즉시 새 키로 전환됩니다.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Actions Footer */}
            <div className="pt-2 flex items-center justify-end space-x-2 shrink-0">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
              >
                닫기
              </button>
              <button
                type="submit"
                disabled={saving}
                className="flex items-center space-x-1.5 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all disabled:opacity-50"
              >
                {saving ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Save className="w-3.5 h-3.5" />
                )}
                <span>{saving ? '저장 중...' : '설정 저장 (서버 무중단 즉시 적용)'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
