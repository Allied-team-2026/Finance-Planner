export default function Navbar({
  session,
  onResetSession,
  onNavigateWorkspace,
  viewMode,
}) {
  const isGuest = !session || session.mode === 'guest'
  const isDemo = session?.mode === 'authenticated_demo'
  const customer = session?.customer
  // The verifier's own verdict drives the colour. A green dot over a failed
  // audit is worse than no dot at all.
  const auditFailed = customer?.verifier?.status === 'fail'

  return (
    <header className="border-b border-slate-800/80 bg-[#0c121e]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Brand Logo & Name */}
          <div
            onClick={onResetSession}
            className="flex items-center gap-3 cursor-pointer select-none"
            title="Return to Welcome screen"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 shadow-md shadow-indigo-500/20">
              <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold tracking-tight text-white">Cognizant</span>
                <span className="rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/20">
                  WealthIQ
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Autonomous Financial Planning & Stress Engine</p>
            </div>
          </div>

          {/* Engine & Verification Trust Badges */}
          <div className="hidden md:flex items-center gap-3 text-xs">
            <div className="flex items-center gap-2 rounded-lg bg-slate-900/80 px-3 py-1.5 border border-slate-800 text-slate-300">
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  auditFailed ? 'bg-rose-400' : 'bg-emerald-400'
                }`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${
                  auditFailed ? 'bg-rose-500' : 'bg-emerald-500'
                }`}></span>
              </span>
              <span className="text-slate-400">Auditor:</span>
              <span className={`font-medium capitalize ${auditFailed ? 'text-rose-400' : 'text-emerald-400'}`}>
                {customer?.verifier?.status ?? '—'}
              </span>
            </div>

            <div className="flex items-center gap-2 rounded-lg bg-slate-900/80 px-3 py-1.5 border border-slate-800 text-slate-400">
              <svg className="h-3.5 w-3.5 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
              <span>
                {customer?.meta?.n_simulations == null
                  ? 'Monte Carlo engine'
                  : `${customer.meta.n_simulations.toLocaleString('en-IN')} Monte Carlo Runs`}
              </span>
            </div>

            {/* Customer Session Badge - ONLY displayed when session exists */}
            {!isGuest && customer && (
              isDemo ? (
                <div className="rounded-lg bg-amber-500/10 px-2.5 py-1.5 border border-amber-500/25 text-amber-300 font-mono text-[11px] flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                  <span>Demo Mode &middot; {customer.customer_id ?? '—'}</span>
                </div>
              ) : (
                <div className="rounded-lg bg-slate-900/80 px-2.5 py-1.5 border border-slate-800 text-slate-400 font-mono text-[11px]">
                  ID: {customer.customer_id} {customer.generated_at ? `· ${customer.generated_at}` : ''}
                </div>
              )
            )}

            {/* Back to Workspace button when inside deep analysis */}
            {viewMode === 'dashboard' && onNavigateWorkspace && (
              <button
                type="button"
                onClick={onNavigateWorkspace}
                className="rounded-lg bg-slate-850 hover:bg-slate-800 text-slate-300 border border-slate-750 px-2.5 py-1.5 text-xs font-semibold transition cursor-pointer"
              >
                ← Workspace
              </button>
            )}

            {/* Clear Session / Reset */}
            {!isGuest && onResetSession && (
              <button
                type="button"
                onClick={onResetSession}
                className="rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/20 px-2.5 py-1.5 text-xs font-semibold transition cursor-pointer"
              >
                End Session
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
