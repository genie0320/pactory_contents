import { PenTool, Edit3, BookOpen, Database, Sparkles, RotateCcw, Lock } from 'lucide-react';
import { useDraftStore } from '../store/useDraftStore';

export type NavTab = 'generator' | 'editor' | 'library' | 'inbox' | 'style';

interface NavbarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  onOpenAuth: () => void;
}

export const Navbar = ({ currentTab, onSelectTab, onOpenAuth }: NavbarProps) => {
  const resetDraft = useDraftStore((s) => s.resetDraft);

  const handleNewDraft = () => {
    if (window.confirm('현재 작성 중인 입력 내용을 초기화하고 새 글을 시작하시겠습니까?')) {
      resetDraft();
      onSelectTab('generator');
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onSelectTab('generator')}>
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              P
            </div>
            <div>
              <span className="font-bold text-lg text-slate-900 tracking-tight">Pactory Studio</span>
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
                v2.0
              </span>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {/* Primary Writing Workflows */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl">
              <button
                onClick={() => onSelectTab('generator')}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                  currentTab === 'generator'
                    ? 'bg-white text-indigo-600 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <PenTool className="w-4 h-4" />
                <span>새 글 생성</span>
              </button>

              <button
                onClick={() => onSelectTab('editor')}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                  currentTab === 'editor'
                    ? 'bg-white text-indigo-600 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <Edit3 className="w-4 h-4" />
                <span>스튜디오 에디터</span>
              </button>

              <button
                onClick={() => onSelectTab('library')}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                  currentTab === 'library'
                    ? 'bg-white text-indigo-600 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <BookOpen className="w-4 h-4" />
                <span>글 보관함</span>
              </button>
            </div>

            {/* Visual Divider */}
            <div className="h-6 w-px bg-slate-200 mx-1" />

            {/* Separated Secondary Management Menus */}
            <div className="flex items-center space-x-1">
              <button
                onClick={() => onSelectTab('inbox')}
                title="새로운 파일이 추가되었을 때 수행하는 간헐적 색인 관리"
                className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  currentTab === 'inbox'
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                <span>색인 관리</span>
              </button>

              <button
                onClick={() => onSelectTab('style')}
                title="퇴고작 기반 문체 페르소나 학습 및 관리"
                className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  currentTab === 'style'
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>문체 학습실</span>
              </button>
            </div>
          </nav>

          {/* Quick Actions */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleNewDraft}
              title="현재 작성 상태를 완전 초기화하고 새 글을 시작합니다."
              className="hidden md:flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg border border-slate-200 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>새 글 시작</span>
            </button>

            <button
              onClick={onOpenAuth}
              title="비밀번호 설정 및 인증"
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
            >
              <Lock className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
