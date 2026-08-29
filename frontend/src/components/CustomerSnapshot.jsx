function formatINR(amount) {
  if (amount == null) return '₹0'
  return `₹${Math.round(amount).toLocaleString('en-IN')}`
}

function formatGoalName(name) {
  if (!name) return 'Goal'
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export default function CustomerSnapshot({ customerName, context, profile, goals, peerCohort }) {
  if (!profile) return null

  // Determine highest-priority goal
  const primaryGoal = Array.isArray(goals) && goals.length > 0
    ? [...goals].sort((a, b) => (a.priority ?? Infinity) - (b.priority ?? Infinity))[0]
    : null

  const {
    net_worth,
    total_assets,
    total_liabilities,
    monthly_income,
    monthly_expense,
    monthly_surplus,
    risk_capacity,
    emergency_fund_months,
  } = profile

  const savingsRate = Math.round((monthly_surplus / (monthly_income || 1)) * 100)

  return (
    <section className="rounded-2xl border border-slate-800/80 bg-gradient-to-b from-[#111726]/90 via-[#0e1422]/90 to-[#0a0f1a]/90 p-5 shadow-xl backdrop-blur-md">
      {/* Top Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4 mb-4">
        {/* Left: Customer Info */}
        <div className="flex items-center gap-3.5">
          <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 font-bold text-white shadow-md shadow-indigo-500/20 text-base">
            {customerName ? customerName.charAt(0) : 'R'}
            <span className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-[#111726] bg-emerald-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-white">{customerName}</h2>
              {context && (
                <span className="rounded-md bg-slate-800/80 px-2 py-0.5 text-[11px] font-medium text-slate-300 border border-slate-700/50 capitalize">
                  {context.age}y &middot; {context.employment_type} &middot; {context.city_tier}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Personalized Wealth Profile &middot; Validated Cash Flow
            </p>
          </div>
        </div>

        {/* Right: Primary Goal Badge */}
        {primaryGoal && (
          <div className="flex items-center gap-3 rounded-xl bg-[#141d30] px-4 py-2 border border-slate-700/60 shadow-inner">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400">
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <circle cx="12" cy="12" r="10" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <div className="text-right sm:text-left">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Primary Goal:</span>
                <span className="text-xs font-bold text-white">{formatGoalName(primaryGoal.name)}</span>
              </div>
              <p className="text-xs font-semibold text-indigo-400">
                {formatINR(primaryGoal.target_amount)} <span className="text-slate-400 font-normal">in {primaryGoal.years} years</span>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Financial Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {/* Net Worth */}
        <div className="rounded-xl bg-[#0d1322]/80 p-3.5 border border-slate-800 hover:border-slate-700 transition">
          <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Net Worth</p>
          <p className="mt-1 text-lg font-bold text-white tracking-tight">{formatINR(net_worth)}</p>
          <div className="mt-1 flex items-center justify-between text-[10px] text-slate-400">
            <span>Assets: {formatINR(total_assets)}</span>
            <span>Debt: {formatINR(total_liabilities)}</span>
          </div>
        </div>

        {/* Monthly Income */}
        <div className="rounded-xl bg-[#0d1322]/80 p-3.5 border border-slate-800 hover:border-slate-700 transition">
          <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Monthly Income</p>
          <p className="mt-1 text-lg font-bold text-white tracking-tight">{formatINR(monthly_income)}</p>
          <div className="mt-1 text-[10px] text-slate-400">
            <span>Expense: {formatINR(monthly_expense)}</span>
          </div>
        </div>

        {/* Monthly Surplus - Prominently Highlighted */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-emerald-950/40 via-[#0e1d20] to-[#0c181c] p-3.5 border-2 border-emerald-500/70 shadow-lg shadow-emerald-950/40">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">Monthly Surplus</p>
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <p className="mt-1 text-xl font-extrabold text-emerald-300 tracking-tight">{formatINR(monthly_surplus)}</p>
          <div className="mt-1 flex items-center gap-1 text-[10px] font-medium text-emerald-400/90">
            <span>{savingsRate}% savings rate</span>
            {peerCohort && <span className="text-slate-400">&middot; Top {100 - peerCohort.savings_rate_percentile}% peer rank</span>}
          </div>
        </div>

        {/* Risk Capacity */}
        <div className="rounded-xl bg-[#0d1322]/80 p-3.5 border border-slate-800 hover:border-slate-700 transition">
          <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Risk Capacity</p>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-lg font-bold capitalize text-white">{risk_capacity}</span>
          </div>
          <p className="mt-1 text-[10px] text-slate-400 truncate">1 Dependent + Active EMI</p>
        </div>

        {/* Emergency Fund */}
        <div className="rounded-xl bg-[#0d1322]/80 p-3.5 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Emergency Fund</p>
            {emergency_fund_months < 1 && (
              <span className="rounded bg-rose-500/10 px-1 py-0.5 text-[9px] font-bold text-rose-400 border border-rose-500/20">
                Low
              </span>
            )}
          </div>
          <p className="mt-1 text-lg font-bold text-white tracking-tight">
            {emergency_fund_months} <span className="text-sm font-normal text-slate-400">{emergency_fund_months === 1 ? 'month' : 'months'}</span>
          </p>
          <p className="mt-1 text-[10px] text-amber-400">Target: 3–6 months buffer</p>
        </div>

        {/* Horizon & Benchmark */}
        <div className="rounded-xl bg-[#0d1322]/80 p-3.5 border border-slate-800 hover:border-slate-700 transition">
          <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Planning Horizon</p>
          <p className="mt-1 text-lg font-bold text-white tracking-tight">{primaryGoal ? primaryGoal.years : 5} Years</p>
          <p className="mt-1 text-[10px] text-slate-400 truncate">
            {peerCohort ? `Matched vs ${peerCohort.cohort_size} peers` : 'Goal-weighted horizon'}
          </p>
        </div>
      </div>
    </section>
  )
}
