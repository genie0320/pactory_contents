import { useState, useEffect } from 'react';
import { BookOpen, Trash2, Search } from 'lucide-react';
import { editorApi } from '../api/client';
import type { CreationSummaryItem } from '../api/client';

interface LibraryPageProps {
  onOpenCreation: (creationId: string) => void;
}

export const LibraryPage = ({ onOpenCreation }: LibraryPageProps) => {
  const [creations, setCreations] = useState<CreationSummaryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadCreations = async () => {
    setLoading(true);
    try {
      const items = await editorApi.listCreations(statusFilter || undefined);
      setCreations(items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCreations();
  }, [statusFilter]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('정말 이 글을 삭제하시겠습니까?')) {
      try {
        await editorApi.deleteCreation(id);
        setCreations((prev) => prev.filter((c) => c.creation_id !== id));
      } catch (err) {
        alert('삭제에 실패했습니다.');
      }
    }
  };

  const filteredCreations = creations.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.topic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-6 border-b border-slate-200 gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">내 글 보관함 (Library)</h1>
          <p className="text-xs text-slate-500 mt-1">
            작성 중인 초안 및 퇴고가 완료된 아티클 목록입니다. 클릭하여 에디터에서 바로 열어볼 수 있습니다.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Status filter tabs */}
          <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setStatusFilter('')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                statusFilter === '' ? 'bg-white text-indigo-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              전체
            </button>
            <button
              onClick={() => setStatusFilter('FINALIZED')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                statusFilter === 'FINALIZED' ? 'bg-white text-indigo-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              퇴고 완료
            </button>
            <button
              onClick={() => setStatusFilter('DRAFT')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                statusFilter === 'DRAFT' ? 'bg-white text-indigo-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              초안 상태
            </button>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative mb-6">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="제목 또는 주제 검색..."
          className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {loading ? (
        <div className="py-16 text-center text-xs text-slate-400">보관함 불러오는 중...</div>
      ) : filteredCreations.length === 0 ? (
        <div className="py-20 text-center bg-white rounded-2xl border border-slate-200 p-8">
          <BookOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <h3 className="font-bold text-slate-700 text-sm">보관된 글이 없습니다.</h3>
          <p className="text-xs text-slate-400 mt-1">새 글 생성기에서 새로운 초안을 완성해보세요.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCreations.map((c) => {
            const isFinal = c.status === 'FINALIZED';
            return (
              <div
                key={c.creation_id}
                onClick={() => onOpenCreation(c.creation_id)}
                className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${
                        isFinal
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                          : 'bg-amber-50 text-amber-700 border border-amber-100'
                      }`}
                    >
                      {isFinal ? '✓ 퇴고 완료' : '✍️ 초안 상태'}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {c.created_at ? c.created_at.split('T')[0] : ''}
                    </span>
                  </div>

                  <h3 className="font-bold text-base text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-2 mb-1.5">
                    {c.title}
                  </h3>

                  <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-3">
                    {c.topic}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                  <span>시드 {c.seed_doc_ids?.length || 0}개 활용</span>
                  <button
                    onClick={(e) => handleDelete(c.creation_id, e)}
                    className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
