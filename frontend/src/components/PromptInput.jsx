import React, { useRef, useEffect } from 'react';
import { Sparkles, ArrowRight, CornerDownLeft, XCircle } from 'lucide-react';

const QUICK_SAMPLES = [
  "Show all students who scored more than 80 marks.",
  "Find the top 5 students by GPA.",
  "Show the average marks for each course.",
  "Count the total number of students.",
  "List courses with no enrolled students.",
  "Find students enrolled in more than one course."
];

export default function PromptInput({
  question,
  setQuestion,
  onGenerate,
  isGenerating
}) {
  const textareaRef = useRef(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [question]);

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!isGenerating && question.trim()) {
        onGenerate();
      }
    }
  };

  return (
    <div className="space-y-3">
      {/* Input container */}
      <div className="relative rounded-2xl border transition-all duration-200 border-slate-700/80 bg-slate-900/90 shadow-lg shadow-black/20 focus-within:border-sky-500/80 focus-within:ring-2 focus-within:ring-sky-500/20 light:bg-white light:border-slate-300 light:shadow-slate-200/50">
        <div className="p-3.5 pb-2">
          <textarea
            ref={textareaRef}
            id="natural-language-input"
            rows={2}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question in plain English (e.g., 'Show all students who scored more than 80 marks')..."
            className="w-full bg-transparent resize-none outline-none text-sm placeholder:text-slate-500 text-slate-100 light:text-slate-900 font-normal leading-relaxed"
          />
        </div>

        {/* Action bar below textarea */}
        <div className="px-3.5 pb-2.5 pt-1 flex items-center justify-between border-t border-slate-800/60 light:border-slate-100">
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <span className="hidden sm:inline">Press</span>
            <kbd className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 border border-slate-700 light:bg-slate-100 light:border-slate-300 text-slate-400">
              Ctrl + Enter
            </kbd>
            <span className="hidden sm:inline">to generate</span>
          </div>

          <div className="flex items-center space-x-2">
            {question && (
              <button
                type="button"
                onClick={() => setQuestion('')}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 light:hover:text-slate-700 transition-colors"
                title="Clear question"
              >
                <XCircle className="w-4 h-4" />
              </button>
            )}

            <button
              id="generate-sql-button"
              type="button"
              disabled={isGenerating || !question.trim()}
              onClick={onGenerate}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all duration-150 ${
                isGenerating || !question.trim()
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
                  : 'bg-gradient-to-r from-sky-500 to-indigo-600 text-white shadow-md shadow-sky-500/25 hover:from-sky-400 hover:to-indigo-500 active:scale-95'
              }`}
            >
              {isGenerating ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Generating SQL...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Generate SQL</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Example question chips */}
      <div className="flex flex-wrap items-center gap-1.5 pt-1">
        <span className="text-[11px] font-medium text-slate-400 light:text-slate-500 mr-1 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-sky-400" />
          Try:
        </span>
        {QUICK_SAMPLES.map((sample, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setQuestion(sample)}
            className="text-[11px] px-2.5 py-1 rounded-full border transition-all duration-150 text-slate-300 border-slate-700/60 bg-slate-800/40 hover:bg-slate-800 hover:border-sky-500/40 hover:text-sky-300 light:bg-slate-100 light:border-slate-200 light:text-slate-700 light:hover:bg-slate-200"
          >
            {sample}
          </button>
        ))}
      </div>
    </div>
  );
}
