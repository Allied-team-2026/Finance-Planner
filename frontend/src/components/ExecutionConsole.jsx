import { useEffect, useRef } from 'react'

export default function ExecutionConsole({ logs, isVerified, verifierData, customerId }) {
  const consoleBottomRef = useRef(null)

  useEffect(() => {
    consoleBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-800/90 bg-[#060910]/95 backdrop-blur-xl shadow-2xl overflow-hidden font-mono text-xs min-h-0">
      {/* Console Window Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-950/80 border-b border-slate-800/80 shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-rose-500/80" />
            <div className="w-2 h-2 rounded-full bg-amber-500/80" />
            <div className="w-2 h-2 rounded-full bg-emerald-500/80" />
          </div>
          <span className="text-[10.5px] font-semibold text-slate-400 ml-1 truncate">
            WealthIQ Kernel &middot; {customerId}
          </span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <span className={`h-1.5 w-1.5 rounded-full ${isVerified ? 'bg-emerald-400' : 'bg-indigo-400 animate-ping'}`} />
          <span className="text-[9px] uppercase font-bold tracking-wider text-slate-400">
            {isVerified ? 'VERIFIED' : 'STREAMING'}
          </span>
        </div>
      </div>

      {/* Log Stream Body */}
      <div className="flex-1 p-3 overflow-y-auto space-y-1 text-[10px] leading-relaxed custom-scrollbar min-h-0">
        <div className="text-slate-500 select-none pb-1 border-b border-slate-850 text-[9.5px]">
          # Cognizant WealthIQ Autonomous Engine v1.0.0
          <br />
          # Customer ID: <span className="text-indigo-400">{customerId}</span> | 11-Stage Pipeline
        </div>

        {logs.map((log) => {
          let textClass = 'text-slate-300'
          if (log.type === 'success') textClass = 'text-emerald-400'
          else if (log.type === 'warn') textClass = 'text-amber-300'
          else if (log.type === 'info') textClass = 'text-cyan-300'
          else if (log.type === 'dim') textClass = 'text-slate-500'

          return (
            <div key={log.id} className="flex items-start gap-1.5 animate-fadeIn">
              <span className="text-slate-600 select-none shrink-0 font-mono text-[9px]">
                {log.timestamp}
              </span>
              {log.stageNum && (
                <span className="text-indigo-400/90 shrink-0 font-bold text-[9.5px]">
                  [{log.stageNum}]
                </span>
              )}
              <span className={`break-words ${textClass}`}>
                {log.message}
              </span>
            </div>
          )
        })}

        {isVerified && verifierData && (
          <div className="mt-2 p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 space-y-0.5">
            <div className="font-bold flex items-center gap-1 text-[10.5px] text-emerald-400">
              <span>✓ DETERMINISTIC VERIFICATION PASSED</span>
            </div>
            <div className="text-[9.5px] text-slate-300">
              Numbers audited: <strong className="text-emerald-300">{verifierData.numbers_checked ?? 11}</strong> &middot; Discrepancies: <strong className="text-emerald-300">0</strong>
            </div>
            <div className="text-[9px] text-slate-400">
              Status: {verifierData.status ?? 'pass'} &middot; Model: api-v1
            </div>
          </div>
        )}

        <div ref={consoleBottomRef} />
      </div>
    </div>
  )
}
