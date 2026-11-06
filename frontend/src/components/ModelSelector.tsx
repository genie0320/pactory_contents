import React from 'react';
import { Cpu } from 'lucide-react';

export interface ModelOption {
  id: string;
  name: string;
  badge: string;
}

export const AVAILABLE_MODELS: ModelOption[] = [
  { id: 'gemini-3.5-flash-lite', name: 'Gemini 3.5 Flash-Lite', badge: '고속/경량' },
  { id: 'gemini-3.8-flash', name: 'Gemini 3.8 Flash', badge: '추천/고품질' },
  { id: 'gemini-3.8-pro', name: 'Gemini 3.8 Pro', badge: '심층/최상위' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', badge: 'OpenAI' },
  { id: 'claude-3-7-sonnet-latest', name: 'Claude 3.7 Sonnet', badge: 'Anthropic' },
];

interface ModelSelectorProps {
  value: string;
  onChange: (model: string) => void;
  disabled?: boolean;
  className?: string;
  labelPrefix?: string;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  className = '',
  labelPrefix = 'AI 모델:',
}) => {
  return (
    <div className={`inline-flex items-center space-x-1.5 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 shadow-2xs ${className}`}>
      <Cpu className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
      {labelPrefix && (
        <span className="text-[11px] font-bold text-slate-500 shrink-0">{labelPrefix}</span>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="bg-transparent text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer disabled:opacity-50"
      >
        {AVAILABLE_MODELS.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name} [{m.badge}]
          </option>
        ))}
      </select>
    </div>
  );
};
