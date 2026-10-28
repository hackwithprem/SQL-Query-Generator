import React, { useState } from 'react';
import { 
  X, 
  Search, 
  Table2, 
  Key, 
  Link2, 
  Database,
  ArrowRight
} from 'lucide-react';

export default function SchemaExplorerModal({
  isOpen,
  onClose,
  schema,
  onSelectTableQuery
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTable, setActiveTable] = useState(null);

  if (!isOpen) return null;

  const tables = schema?.tables || [];
  
  // Filter tables
  const filteredTables = tables.filter(t => 
    t.table_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.columns.some(c => c.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const selectedTable = activeTable 
    ? tables.find(t => t.table_name === activeTable) 
    : (filteredTables[0] || tables[0]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-4xl h-[85vh] rounded-2xl border flex flex-col overflow-hidden shadow-2xl border-slate-800 bg-slate-900 text-slate-100 light:bg-white light:border-slate-200 light:text-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">Database Schema Explorer</h3>
              <p className="text-xs text-slate-400 light:text-slate-500">
                Connected Dialect: <span className="font-mono text-sky-400 uppercase">{schema?.dialect || 'SQLITE'}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 light:hover:text-slate-800 light:hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-3 border-b border-slate-800 bg-slate-950/40 light:border-slate-200 light:bg-slate-50/50">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search tables or columns (e.g., students, gpa, marks)..."
              className="w-full pl-9 pr-4 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700/60 outline-none text-slate-100 placeholder:text-slate-500 focus:border-sky-500 light:bg-white light:border-slate-300 light:text-slate-900"
            />
          </div>
        </div>

        {/* Body Split: Table List & Table Details */}
        <div className="flex-1 flex overflow-hidden">
          {/* Tables List */}
          <div className="w-64 border-r overflow-y-auto p-3 space-y-1.5 border-slate-800 bg-slate-950/20 light:border-slate-200">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-2 py-1">
              Tables ({filteredTables.length})
            </p>
            {filteredTables.map((tbl) => {
              const isSelected = selectedTable?.table_name === tbl.table_name;
              return (
                <button
                  key={tbl.table_name}
                  onClick={() => setActiveTable(tbl.table_name)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs text-left transition-all ${
                    isSelected
                      ? 'bg-sky-500/15 border border-sky-500/40 text-sky-300 font-semibold light:bg-sky-50 light:text-sky-700'
                      : 'text-slate-300 hover:bg-slate-800/60 light:text-slate-700 light:hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <Table2 className="w-4 h-4 shrink-0 text-slate-400" />
                    <span className="truncate">{tbl.table_name}</span>
                  </div>
                  {tbl.row_count !== null && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 light:bg-slate-200 light:text-slate-600">
                      {tbl.row_count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Table Details */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {selectedTable ? (
              <>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 light:border-slate-200">
                  <div>
                    <h4 className="text-base font-bold text-slate-100 light:text-slate-900 flex items-center gap-2">
                      <span>{selectedTable.table_name}</span>
                      <span className="text-xs font-normal font-mono text-slate-400">
                        ({selectedTable.columns.length} columns &bull; {selectedTable.row_count ?? 0} rows)
                      </span>
                    </h4>
                  </div>
                  {onSelectTableQuery && (
                    <button
                      onClick={() => {
                        onSelectTableQuery(`SELECT * FROM ${selectedTable.table_name} LIMIT 25;`);
                        onClose();
                      }}
                      className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-sky-400 bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 transition-colors"
                    >
                      <span>Query Table</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Columns Table */}
                <div className="space-y-2">
                  <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Columns Definition
                  </h5>
                  <div className="rounded-xl border border-slate-800 overflow-hidden light:border-slate-200">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 light:bg-slate-100 light:border-slate-200">
                        <tr>
                          <th className="py-2.5 px-3 font-medium">Column Name</th>
                          <th className="py-2.5 px-3 font-medium">Data Type</th>
                          <th className="py-2.5 px-3 font-medium text-center">Primary Key</th>
                          <th className="py-2.5 px-3 font-medium text-center">Nullable</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 light:divide-slate-200">
                        {selectedTable.columns.map((col) => (
                          <tr key={col.name} className="hover:bg-slate-800/30 light:hover:bg-slate-50">
                            <td className="py-2 px-3 font-mono text-sky-300 font-medium light:text-sky-700 flex items-center gap-1.5">
                              {col.primary_key && <Key className="w-3 h-3 text-amber-400 shrink-0" />}
                              <span>{col.name}</span>
                            </td>
                            <td className="py-2 px-3 font-mono text-slate-400">{col.type}</td>
                            <td className="py-2 px-3 text-center">
                              {col.primary_key ? (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                                  PK
                                </span>
                              ) : (
                                <span className="text-slate-600">-</span>
                              )}
                            </td>
                            <td className="py-2 px-3 text-center text-slate-400">
                              {col.nullable ? 'Yes' : 'No'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Foreign Keys / Relationships */}
                {selectedTable.foreign_keys && selectedTable.foreign_keys.length > 0 && (
                  <div className="space-y-2">
                    <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <Link2 className="w-3.5 h-3.5 text-indigo-400" />
                      Foreign Key Relationships
                    </h5>
                    <div className="space-y-1.5">
                      {selectedTable.foreign_keys.map((fk, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/40 text-xs font-mono text-slate-300 light:bg-slate-50 light:border-slate-200 light:text-slate-700 flex items-center gap-2"
                        >
                          <span className="text-sky-300">({fk.constrained_columns.join(', ')})</span>
                          <span className="text-slate-500">&rarr;</span>
                          <span className="text-emerald-400 font-semibold">{fk.referred_table}</span>
                          <span className="text-sky-300">({fk.referred_columns.join(', ')})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="p-12 text-center text-xs text-slate-500">
                Select a table from the left to view its schema details.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
