import React, { useState } from 'react';
import { 
  Table, 
  Clock, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  Inbox, 
  CheckCircle2, 
  Layers
} from 'lucide-react';

export default function ResultsTable({
  results,
  isLoading,
  error
}) {
  const [page, setPage] = useState(1);
  const rowsPerPage = 10;

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12 flex flex-col items-center justify-center space-y-3 light:bg-white light:border-slate-200">
        <div className="w-8 h-8 border-3 border-sky-500/30 border-t-sky-500 rounded-full animate-spin" />
        <p className="text-xs font-medium text-slate-400">Executing query against database...</p>
      </div>
    );
  }

  if (!results && !error) {
    return (
      <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-12 flex flex-col items-center justify-center text-center space-y-2 light:bg-white light:border-slate-200">
        <div className="w-12 h-12 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-center text-slate-500 light:bg-slate-100 light:border-slate-300">
          <Table className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-300 light:text-slate-700">No Query Results Yet</h4>
        <p className="text-xs text-slate-500 max-w-sm">
          Generate an SQL query and click "Execute Query" to inspect records returned by the database.
        </p>
      </div>
    );
  }

  if (error) {
    return null; // Handled by ErrorCorrectionCard
  }

  const columns = results.columns || [];
  const rows = results.rows || [];
  const totalRows = results.row_count || 0;
  const duration = results.duration_ms || 0;
  const isTruncated = results.truncated;

  // Pagination calculation
  const totalPages = Math.ceil(rows.length / rowsPerPage) || 1;
  const displayedRows = rows.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  const exportCSV = () => {
    if (rows.length === 0) return;
    const header = columns.join(',');
    const csvRows = rows.map(r => 
      columns.map(c => {
        const val = r[c] === null || r[c] === undefined ? '' : String(r[c]);
        return `"${val.replace(/"/g, '""')}"`;
      }).join(',')
    );
    const blob = new Blob([[header, ...csvRows].join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `query_results_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="rounded-2xl border flex flex-col border-slate-800 bg-slate-900/90 shadow-xl overflow-hidden light:bg-white light:border-slate-200">
      {/* Table Header / Stats Bar */}
      <div className="px-5 py-3 border-b flex flex-wrap items-center justify-between gap-3 border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs text-slate-300 light:text-slate-700 font-medium">
            <Layers className="w-4 h-4 text-sky-400" />
            <span>Returned Records</span>
          </div>

          <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 light:bg-slate-200 light:border-slate-300 text-slate-300 light:text-slate-800">
            {totalRows} {totalRows === 1 ? 'row' : 'rows'}
          </span>

          <div className="flex items-center space-x-1 text-xs text-slate-400 font-mono">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>{duration} ms</span>
          </div>

          {isTruncated && (
            <span className="text-[11px] text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/20">
              Truncated at limit
            </span>
          )}
        </div>

        {/* CSV Export Action */}
        {rows.length > 0 && (
          <button
            type="button"
            onClick={exportCSV}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 border border-slate-700 light:bg-white light:border-slate-300 light:text-slate-700 light:hover:bg-slate-100 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-sky-400" />
            <span>Export CSV</span>
          </button>
        )}
      </div>

      {/* Table Content or Empty State */}
      {rows.length === 0 ? (
        <div className="p-12 flex flex-col items-center justify-center space-y-2 text-center">
          <Inbox className="w-8 h-8 text-slate-600" />
          <h5 className="text-xs font-semibold text-slate-400">Query Executed Successfully</h5>
          <p className="text-xs text-slate-500">The query ran in {duration} ms, but returned 0 records matching the criteria.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/40 light:border-slate-200 light:bg-slate-100/70">
                <th className="py-2.5 px-4 font-mono font-semibold text-slate-500 text-[11px] w-12 text-center">#</th>
                {columns.map((col, idx) => (
                  <th
                    key={idx}
                    className="py-2.5 px-4 font-semibold text-slate-300 light:text-slate-700 tracking-wider font-mono text-[11px]"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 light:divide-slate-200">
              {displayedRows.map((row, rIdx) => (
                <tr
                  key={rIdx}
                  className="hover:bg-slate-800/30 light:hover:bg-slate-50 transition-colors"
                >
                  <td className="py-2 px-4 text-center text-slate-500 font-mono text-[11px]">
                    {(page - 1) * rowsPerPage + rIdx + 1}
                  </td>
                  {columns.map((col, cIdx) => {
                    const val = row[col];
                    const isNull = val === null || val === undefined;
                    return (
                      <td
                        key={cIdx}
                        className={`py-2 px-4 whitespace-nowrap text-xs ${
                          isNull
                            ? 'text-slate-600 italic font-mono'
                            : typeof val === 'number'
                            ? 'text-sky-300 font-mono light:text-sky-700'
                            : 'text-slate-200 light:text-slate-800'
                        }`}
                      >
                        {isNull ? 'NULL' : String(val)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="px-4 py-2.5 border-t flex items-center justify-between text-xs border-slate-800 bg-slate-950/40 light:border-slate-200 light:bg-slate-50">
          <div className="text-slate-500">
            Showing {(page - 1) * rowsPerPage + 1} - {Math.min(page * rowsPerPage, rows.length)} of {rows.length} rows
          </div>
          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1 rounded-md border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed light:bg-white light:border-slate-300 light:text-slate-600"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-mono text-[11px] text-slate-400">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1 rounded-md border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed light:bg-white light:border-slate-300 light:text-slate-600"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
