import { useState } from 'react';
import { Lock, X, ShieldCheck } from 'lucide-react';
import { authApi } from '../api/client';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AuthModal = ({ isOpen, onClose, onSuccess }: AuthModalProps) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authApi.login(password);
      localStorage.setItem('pactory_studio_password', password);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || '비밀번호가 일치하지 않습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-2 text-indigo-600">
            <Lock className="w-5 h-5" />
            <h3 className="font-bold text-slate-900 text-lg">Pactory Studio 인증</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="mt-4 text-xs text-slate-500 leading-relaxed">
          외부 원격 접속 및 중요 API 접근 보호를 위해 설정된 Studio 비밀번호를 입력해주세요.
        </p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">비밀번호</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Studio 비밀번호 입력"
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              autoFocus
            />
          </div>

          {error && <div className="p-3 text-xs text-rose-600 bg-rose-50 rounded-lg">{error}</div>}

          <div className="flex items-center justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading || !password}
              className="flex items-center space-x-1 px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg transition-colors shadow-xs"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{loading ? '인증 중...' : '확인'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
