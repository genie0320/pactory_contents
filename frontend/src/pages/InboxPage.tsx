import { useState, useEffect } from 'react';
import { Database, RefreshCw, CheckCircle2, FileText } from 'lucide-react';
import { inboxApi } from '../api/client';
import type { ArticleSummaryItem, InboxScanResponse } from '../api/client';

export const InboxPage = () => {
  const [scanData, setScanData] = useState<InboxScanResponse | null>(null);
  const [articles, setArticles] = useState<ArticleSummaryItem[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processMessage, setProcessMessage] = useState('');

  const loadData = async () => {
    setIsScanning(true);
    try {
      const [scanRes, articlesRes, statsRes] = await Promise.all([
        inboxApi.scan(),
        inboxApi.listArticles(100),
        inboxApi.getStats(),
      ]);
      setScanData(scanRes);
      setArticles(articlesRes.items);
      setStats(statsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleProcess = async () => {
    setIsProcessing(true);
    setProcessMessage('');
    try {
      const res = await inboxApi.process(false, false);
      setProcessMessage(res.message);
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '색인 처리 중 오류가 발생했습니다.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Intermittent Management Banner */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-xs flex items-start space-x-4">
        <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 text-indigo-400">
          <Database className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h2 className="font-bold text-base">소재 색인 관리 (Knowledge Index Manager)</h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            색인 관리는 새로운 문서(PDF, Markdown, TXT)가 <code className="px-1.5 py-0.5 bg-slate-800 rounded text-indigo-300 font-mono">data/inbox/</code>에 추가되었을 때만 실행하는 <strong>간헐적 배치 작업</strong>입니다. 이미 색인된 데이터는 '새 글 생성기'의 시드 풀에서 즉시 활용됩니다.
          </p>
        </div>
      </div>

      {/* Summary Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">인박스 대기 파일</span>
          <div className="text-2xl font-extrabold text-slate-900 mt-1">
            {scanData?.total_files || 0}
            <span className="text-xs font-normal text-slate-500 ml-1.5">
              (미색인: {scanData?.unindexed_files || 0})
            </span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">DB 색인 완료 아티클</span>
          <div className="text-2xl font-extrabold text-indigo-600 mt-1">
            {stats?.indexed_articles || 0}
            <span className="text-xs font-normal text-slate-500 ml-1.5">편</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500">누적 생성 아티클</span>
          <div className="text-2xl font-extrabold text-emerald-600 mt-1">
            {stats?.total_creations || 0}
            <span className="text-xs font-normal text-slate-500 ml-1.5">편</span>
          </div>
        </div>
      </div>

      {processMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-xs font-bold text-emerald-800">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{processMessage}</span>
        </div>
      )}

      {/* Inbox Files Actions & List */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">data/inbox 폴더 상태</h3>
            <p className="text-[11px] text-slate-400">새 파일을 inbox 폴더에 넣고 아래 버튼을 누르면 색인 처리가 진행됩니다.</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadData}
              disabled={isScanning}
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={handleProcess}
              disabled={isProcessing || !scanData || scanData.total_files === 0}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition-all shadow-xs flex items-center space-x-1.5"
            >
              <span>{isProcessing ? '색인 및 임베딩 처리 중...' : '📥 신규 파일 색인 처리'}</span>
            </button>
          </div>
        </div>

        {scanData?.files && scanData.files.length > 0 ? (
          <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
            {scanData.files.map((f, idx) => (
              <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-slate-800">{f.filename}</span>
                  <span className="text-[11px] text-slate-400">({(f.size_bytes / 1024).toFixed(1)} KB)</span>
                </div>
                <div>
                  {f.is_indexed ? (
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-md text-[11px] font-bold">
                      색인 완료 (#{f.doc_id})
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded-md text-[11px] font-bold">
                      대기 중 (미색인)
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-400">
            inbox 폴더에 처리 대기 중인 파일이 없습니다.
          </div>
        )}
      </div>

      {/* Indexed Articles Catalog */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="font-bold text-slate-900 text-sm">색인 카탈로그 DB (총 {articles.length}편)</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2.5 px-3 font-semibold">ID</th>
                <th className="py-2.5 px-3 font-semibold">제목</th>
                <th className="py-2.5 px-3 font-semibold">글자수</th>
                <th className="py-2.5 px-3 font-semibold">상태</th>
                <th className="py-2.5 px-3 font-semibold">색인 시점</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {articles.map((art) => (
                <tr key={art.doc_id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-mono font-bold text-indigo-600">#{art.doc_id}</td>
                  <td className="py-2.5 px-3 font-medium text-slate-900">{art.title}</td>
                  <td className="py-2.5 px-3 text-slate-500">{art.char_count.toLocaleString()}자</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded-md text-[11px] font-bold ${
                        art.status === 'INDEXED'
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      {art.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                    {art.indexed_at ? art.indexed_at.split('T')[0] : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
