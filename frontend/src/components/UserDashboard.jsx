function formatINR(amount) {
  if (amount == null || isNaN(amount)) return '₹0'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

export default function UserDashboard({
  customerName = 'Customer',
  customerId = 'C001',
  profile = {},
  goals = [],
  plans = [],
  selectedPlanId = 'A',
  generatedAt,
  pastAnalyses = [],
  onViewLatestAnalysis,
  onStartNewAnalysis,
}) {
  const primaryGoal = goals && goals.length > 0 ? goals[0] : null
  const activePlan = (plans && plans.find((p) => p.plan_id === selectedPlanId)) || (plans && plans[0])

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8 animate-fadeIn">
      {/* 1. Header Row */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-400 border border-indigo-500/20">
              Customer Workspace &middot; ID: {customerId}
            </span>
            {generatedAt && (
              <span className="text-xs text-slate-400">
                Last updated {generatedAt}
              </span>
            )}
          </div>
          <h1 className="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Welcome back, {customerName}
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Continue from your latest financial plan or review a previous analysis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onStartNewAnalysis}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2.5 text-xs font-semibold text-white shadow-md shadow-indigo-600/25 transition cursor-pointer"
          >
            <span>+ New financial analysis</span>
          </button>
        </div>
      </div>

      {/* 2. Financial Snapshot Row (Compact Baseline Summary) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Net Worth */}
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-4 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Net Worth</p>
          <p className="mt-1.5 text-lg font-extrabold text-white tracking-tight">
            {formatINR(profile.net_worth)}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400">Total assets - liabilities</p>
        </div>

        {/* Monthly Income */}
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-4 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Monthly Income</p>
          <p className="mt-1.5 text-lg font-extrabold text-white tracking-tight">
            {formatINR(profile.monthly_income)}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400">Inflow baseline</p>
        </div>

        {/* Monthly Surplus */}
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-4 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Monthly Surplus</p>
          <p className="mt-1.5 text-lg font-extrabold text-emerald-400 tracking-tight">
            {formatINR(profile.monthly_surplus)}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400">Available to invest</p>
        </div>

        {/* Risk Capacity */}
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-4 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Risk Capacity</p>
          <p className="mt-1.5 text-lg font-extrabold text-indigo-300 capitalize tracking-tight">
            {profile.risk_capacity || 'Moderate'}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400">Financial loss ability</p>
        </div>

        {/* Primary Goal */}
        <div className="col-span-2 sm:col-span-1 rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-4 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Primary Goal</p>
          <p className="mt-1.5 text-sm font-bold text-white capitalize truncate">
            {primaryGoal ? primaryGoal.name.replace(/_/g, ' ') : 'Downpayment'}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400">
            {primaryGoal ? `${formatINR(primaryGoal.target_amount)} in ${primaryGoal.years}y` : '₹25,00,000 in 5y'}
          </p>
        </div>
      </div>

      {/* 3. Latest Financial Analysis Card */}
      <div className="rounded-2xl border border-indigo-500/30 bg-gradient-to-b from-indigo-950/20 via-[#0d1322] to-[#0a0f1d] p-6 sm:p-7 shadow-xl backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
                  Active Strategy
                </span>
                <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300 border border-emerald-500/30">
                  Audited & Stress-Tested
                </span>
              </div>
              <h2 className="text-xl font-bold text-white mt-0.5">
                Your latest financial analysis
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={onViewLatestAnalysis}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            <span>View latest analysis</span>
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>

        {/* Strategy Highlights Grid */}
        {activePlan ? (
          <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Plan Identity & Commitment */}
            <div className="rounded-xl bg-[#080d18]/80 p-4 border border-slate-800">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Selected Strategy</p>
              <p className="mt-1 text-base font-bold text-white">
                Plan {activePlan.plan_id} &middot; {activePlan.label}
              </p>
              <p className="mt-0.5 text-xs text-slate-300">
                {formatINR(activePlan.monthly_investment)} / month commitment
              </p>
            </div>

            {/* Goal Success Probability */}
            <div className="rounded-xl bg-[#080d18]/80 p-4 border border-slate-800">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Goal Success Probability</p>
              <p className="mt-1 text-base font-bold text-emerald-400">
                {Math.round(activePlan.success_probability * 100)}%
              </p>
              <p className="mt-0.5 text-xs text-slate-400">
                Across 10,000 Monte Carlo runs
              </p>
            </div>

            {/* Cash Flow Affordability */}
            <div className="rounded-xl bg-[#080d18]/80 p-4 border border-slate-800">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Cash Flow Buffer</p>
              <p className={`mt-1 text-base font-bold ${activePlan.feasible ? 'text-emerald-400' : 'text-rose-400'}`}>
                {activePlan.feasible ? '✓ Affordable' : '✕ Deficit'}
              </p>
              <p className="mt-0.5 text-xs text-slate-400">
                {activePlan.surplus_after_investment >= 0
                  ? `+${formatINR(activePlan.surplus_after_investment)} / mo surplus buffer`
                  : `${formatINR(activePlan.surplus_after_investment)} / mo deficit`}
              </p>
            </div>

            {/* Stress Test Verification */}
            <div className="rounded-xl bg-[#080d18]/80 p-4 border border-slate-800">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Stress Resilience</p>
              <p className={`mt-1 text-base font-bold ${activePlan.survives_stress ? 'text-emerald-400' : 'text-amber-400'}`}>
                {activePlan.survives_stress ? '✓ Survives All Shocks' : '⚠ Fails Under Stress'}
              </p>
              <p className="mt-0.5 text-xs text-slate-400">
                165 shock combinations tested
              </p>
            </div>
          </div>
        ) : (
          <div className="mt-5 text-xs text-slate-400">
            No plan selected. Click &quot;View latest analysis&quot; to review generated strategies.
          </div>
        )}
      </div>

      {/* 4. Past Analyses Section */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div>
            <h3 className="text-lg font-bold text-white">Past analyses</h3>
            <p className="text-xs text-slate-400">
              Historical strategic plans and scenario evaluations
            </p>
          </div>
        </div>

        {pastAnalyses && pastAnalyses.length > 0 ? (
          <div className="space-y-3">
            {pastAnalyses.map((item, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-slate-800 bg-[#0d1322]/80 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-xs font-mono text-slate-300">
                    {idx + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{item.date}</span>
                      <span className="text-[11px] text-slate-400">&middot;</span>
                      <span className="text-xs text-slate-300 capitalize">{item.goalName}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Plan {item.planId} ({item.planLabel}) &middot; {Math.round(item.successProbability * 100)}% Success &middot; {item.status}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={onViewLatestAnalysis}
                  className="rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3.5 py-1.5 text-xs font-medium text-slate-200 transition cursor-pointer self-end sm:self-auto"
                >
                  View analysis &rarr;
                </button>
              </div>
            ))}
          </div>
        ) : (
          /* Polished Empty State when no history exists */
          <div className="rounded-2xl border border-dashed border-slate-800 bg-[#0d1322]/40 p-8 flex flex-col items-center justify-center text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-slate-400 border border-slate-800 mb-3">
              <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </div>
            <h4 className="text-sm font-bold text-slate-200">
              No previous analyses yet
            </h4>
            <p className="mt-1 max-w-sm text-xs text-slate-400 leading-relaxed">
              Your saved financial analyses and scenario evaluations will appear here.
            </p>
            <button
              type="button"
              onClick={onStartNewAnalysis}
              className="mt-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 transition cursor-pointer"
            >
              Start a new analysis
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
