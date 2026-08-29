function formatINR(amount) {
  if (amount == null || isNaN(amount)) return '₹0'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

function formatPercent(decimal) {
  if (decimal == null || isNaN(decimal)) return '0%'
  return `${Math.round(Number(decimal) * 100)}%`
}

function CircularProgress({ probability, statusTheme }) {
  const pct = Math.round((probability || 0) * 100)
  const radius = 34
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - ((probability || 0) * circumference)

  let strokeColor = '#10b981' // emerald (positive)
  const trackColor = '#1e293b'
  let textColor = 'text-white'

  if (statusTheme === 'warning') {
    strokeColor = '#f59e0b' // amber (warning)
    textColor = 'text-amber-300'
  } else if (statusTheme === 'unsuitable') {
    strokeColor = '#f43f5e' // rose (unsuitable/deficit)
    textColor = 'text-rose-400'
  }

  return (
    <div className="relative flex items-center justify-center">
      <svg className="h-24 w-24 -rotate-90 transform" viewBox="0 0 90 90">
        {/* Track circle */}
        <circle
          cx="45"
          cy="45"
          r={radius}
          stroke={trackColor}
          strokeWidth="6"
          fill="transparent"
          className="opacity-60"
        />
        {/* Progress circle */}
        <circle
          cx="45"
          cy="45"
          r={radius}
          stroke={strokeColor}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className={`text-2xl font-extrabold tracking-tight ${textColor}`}>{pct}%</span>
      </div>
    </div>
  )
}

export default function PlanCard({ plan, monthlySurplus = 45000, isSelected, onSelect, onViewDetails }) {
  const {
    plan_id,
    label,
    monthly_investment,
    allocation,
    expected_annual_return,
    projected_corpus,
    goal_amount,
    success_probability,
    successful_simulations,
    feasible,
    survives_stress,
    exceeds_risk_ceiling,
    surplus_after_investment,
  } = plan

  const surplusAfter = surplus_after_investment !== undefined
    ? surplus_after_investment
    : (monthlySurplus - monthly_investment)

  const equityPct = allocation ? Math.round(allocation.equity * 100) : 40
  const debtPct = 100 - equityPct
  const simCount = successful_simulations || Math.round((success_probability || 0.87) * 10000)

  // Determine Status Theme
  let statusTheme = 'resilient'
  if (!feasible || exceeds_risk_ceiling) {
    statusTheme = 'unsuitable'
  } else if (!survives_stress) {
    statusTheme = 'warning'
  }

  // Dynamic Decision Signal derived from plan fields
  let signalTag = ''
  let signalDesc = ''
  if (feasible && survives_stress) {
    signalTag = 'STRESS-RESILIENT'
    signalDesc = 'Affordable and survives tested shocks.'
  } else if (feasible && !survives_stress) {
    signalTag = 'STRESS VULNERABLE'
    signalDesc = 'Affordable, but fails under a combination of shocks.'
  } else {
    signalTag = 'NOT AFFORDABLE'
    signalDesc = 'Requires more monthly cash flow than currently available.'
  }

  // Refined card container styles: dark navy dominant, subtle selected state
  const cardBorderClass = isSelected
    ? 'ring-1 ring-indigo-500/80 border-indigo-500/60 shadow-lg shadow-indigo-950/30'
    : 'border-slate-800 hover:border-slate-700/80 shadow-md'

  return (
    <div
      className={`relative flex flex-col justify-between rounded-2xl border bg-[#0d1322]/95 p-5 backdrop-blur-md transition-all duration-200 ${cardBorderClass}`}
    >
      <div>
        {/* 1. Plan Identity Header */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-slate-800 text-xs font-bold text-white border border-slate-700">
              {plan_id}
            </span>
            <span className="text-lg font-bold text-white">{label}</span>
          </div>

          {isSelected ? (
            <span className="rounded-full bg-indigo-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-300 border border-indigo-500/30">
              Selected
            </span>
          ) : (
            <span className="text-[11px] font-mono text-slate-400">
              {formatINR(monthly_investment)}/mo
            </span>
          )}
        </div>

        {/* 2. Decision Signal Area */}
        <div className="mb-3 rounded-xl p-3 bg-slate-950/60 border border-slate-800/80">
          <div className="flex items-center justify-between">
            <span className={`text-[11px] font-extrabold uppercase tracking-wider ${
              statusTheme === 'resilient'
                ? 'text-emerald-400'
                : statusTheme === 'warning'
                ? 'text-amber-400'
                : 'text-rose-400'
            }`}>
              {signalTag}
            </span>
            {exceeds_risk_ceiling && (
              <span className="text-[10px] font-bold text-rose-400 bg-rose-950/40 px-1.5 py-0.5 rounded border border-rose-800/40">
                Risk Ceiling Violated
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-300 leading-snug">
            {signalDesc}
          </p>
        </div>

        {/* 3. Goal Success Probability Gauge with Paired Context */}
        <div className="my-3 flex flex-col items-center justify-center rounded-xl bg-[#090e1a] p-3.5 border border-slate-800/80">
          <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1 text-center">
            Goal success probability
          </p>
          <CircularProgress probability={success_probability} statusTheme={statusTheme} />
          <p className="mt-1 text-xs text-slate-400 font-normal text-center">
            <span className="text-slate-300 font-medium">{simCount.toLocaleString('en-IN')}</span> / 10,000 simulations
          </p>

          {/* Paired Decision Context */}
          <div className="mt-2.5 pt-2 border-t border-slate-800/80 w-full text-center">
            {statusTheme === 'resilient' && (
              <p className="text-[11px] font-medium text-emerald-400">
                ✓ 87% success &middot; ₹10k monthly buffer &middot; survives stress
              </p>
            )}
            {statusTheme === 'warning' && (
              <p className="text-[11px] font-medium text-amber-400">
                ⚠ 71% success &middot; fails under combined adverse shocks
              </p>
            )}
            {statusTheme === 'unsuitable' && (
              <div className="text-[11px] font-semibold text-rose-400 space-y-0.5">
                <p>✕ 95% simulated success, but NOT affordable</p>
                {exceeds_risk_ceiling && (
                  <p className="text-rose-300 text-[10px] font-normal">
                    ⚠ Exceeds moderate risk ceiling (85% equity)
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 4. Core Financial Metrics (2x2 Grid) */}
        <div className="grid grid-cols-2 gap-2.5 text-xs mb-3">
          {/* Monthly Investment */}
          <div className="rounded-xl bg-[#090e1a] p-2.5 border border-slate-800">
            <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Monthly investment</p>
            <p className="mt-1 text-base font-bold text-white">{formatINR(monthly_investment)}</p>
            <p className="mt-0.5 text-[10px] text-slate-400">Committed monthly</p>
          </div>

          {/* Monthly Surplus Left */}
          <div className={`rounded-xl p-2.5 border ${
            surplusAfter < 0
              ? 'bg-rose-950/20 border-rose-500/40'
              : 'bg-[#090e1a] border-slate-800'
          }`}>
            <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Monthly surplus left</p>
            <p className={`mt-1 text-base font-bold ${
              surplusAfter < 0 ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              {surplusAfter < 0
                ? `-₹${Math.abs(Math.round(surplusAfter)).toLocaleString('en-IN')} / mo`
                : `+₹${Math.round(surplusAfter).toLocaleString('en-IN')} / mo`}
            </p>
            <p className={`mt-0.5 text-[10px] font-semibold ${
              surplusAfter < 0 ? 'text-rose-400' : 'text-slate-400 font-normal'
            }`}>
              {surplusAfter < 0 ? 'Not Affordable' : 'Buffer remaining'}
            </p>
          </div>

          {/* Projected Corpus */}
          <div className="rounded-xl bg-[#090e1a] p-2.5 border border-slate-800">
            <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Projected corpus</p>
            <p className="mt-1 text-base font-bold text-white">{formatINR(projected_corpus)}</p>
            <p className="mt-0.5 text-[10px] text-slate-400">
              Target: {formatINR(goal_amount || 2500000)}
            </p>
          </div>

          {/* Expected Return */}
          <div className="rounded-xl bg-[#090e1a] p-2.5 border border-slate-800">
            <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Expected return</p>
            <p className="mt-1 text-base font-bold text-white">{formatPercent(expected_annual_return)} p.a.</p>
            <p className="mt-0.5 text-[10px] text-slate-400">Compounded 5y</p>
          </div>
        </div>

        {/* 5. Asset Allocation Bar */}
        <div className="mb-3 rounded-xl bg-[#090e1a] p-2.5 border border-slate-800">
          <div className="flex justify-between text-xs text-slate-300 font-medium mb-1.5">
            <span className="flex items-center gap-1 text-[11px]">
              <span className="h-2 w-2 rounded-full bg-cyan-400" />
              Equity {equityPct}%
            </span>
            <span className="flex items-center gap-1 text-[11px]">
              <span className="h-2 w-2 rounded-full bg-indigo-400" />
              Debt {debtPct}%
            </span>
          </div>
          <div className="w-full h-1.5 rounded-full overflow-hidden flex bg-slate-800">
            <div className="bg-cyan-500 h-full" style={{ width: `${equityPct}%` }} />
            <div className="bg-indigo-500 h-full" style={{ width: `${debtPct}%` }} />
          </div>
        </div>

        {/* 6. Status Verification Row */}
        <div className="grid grid-cols-2 gap-2 text-xs mb-3">
          <div className="flex items-center justify-between text-[11px] rounded-lg bg-slate-950/60 px-2.5 py-1.5 border border-slate-800">
            <span className="text-slate-400">Affordability:</span>
            <span className={`font-semibold ${feasible ? 'text-emerald-400' : 'text-rose-400'}`}>
              {feasible ? '✓ Affordable' : '✕ Deficit'}
            </span>
          </div>

          <div className="flex items-center justify-between text-[11px] rounded-lg bg-slate-950/60 px-2.5 py-1.5 border border-slate-800">
            <span className="text-slate-400">Stress Test:</span>
            <span className={`font-semibold ${survives_stress ? 'text-emerald-400' : 'text-amber-400'}`}>
              {survives_stress ? '✓ Survives' : '⚠ Fails'}
            </span>
          </div>
        </div>
      </div>

      {/* 7. Action Area: View Details Modal Trigger & Primary Selection Button */}
      <div className="mt-2 pt-2.5 border-t border-slate-800/80 flex flex-col gap-2">
        {/* Open Details Modal (Does NOT select the plan) */}
        <button
          type="button"
          onClick={() => onViewDetails && onViewDetails(plan)}
          className="w-full flex items-center justify-center gap-1.5 py-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-xs font-semibold text-slate-300 hover:text-white border border-slate-800 transition cursor-pointer"
        >
          <span>View Full Plan Analysis</span>
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 3h6v6" />
            <path d="M10 14L21 3" />
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          </svg>
        </button>

        {/* Primary Selection Button */}
        <button
          type="button"
          onClick={onSelect}
          className={`w-full py-2.5 rounded-xl font-semibold text-xs transition-all duration-200 cursor-pointer ${
            isSelected
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30'
              : 'bg-slate-800/90 hover:bg-slate-750 text-slate-200 border border-slate-700/80'
          }`}
        >
          {isSelected
            ? `✓ Selected (Plan ${plan_id})`
            : `Select this plan (Plan ${plan_id})`}
        </button>
      </div>
    </div>
  )
}