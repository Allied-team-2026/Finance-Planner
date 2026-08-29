import { useEffect } from 'react'

function formatINR(amount) {
  if (amount == null || isNaN(amount)) return '₹0'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

function formatPercent(decimal) {
  if (decimal == null || isNaN(decimal)) return '0%'
  return `${Math.round(Number(decimal) * 100)}%`
}

export default function PlanDetailsModal({
  plan,
  monthlySurplus = 45000,
  isSelected = false,
  onSelect,
  onChallenge,
  onWhatIf,
  onClose,
}) {
  // ESC key listener to close modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!plan) return null

  const {
    plan_id,
    label,
    headline,
    body,
    monthly_investment,
    allocation,
    expected_annual_return,
    projected_corpus,
    goal_amount,
    years = 5,
    success_probability,
    successful_simulations,
    feasible,
    survives_stress,
    breaking_combo,
    shortfall_if_hit,
    exceeds_risk_ceiling,
    surplus_after_investment,
    pros = [],
    cons = [],
    p10_corpus,
    median_corpus,
    p90_corpus,
  } = plan

  const surplusAfter = surplus_after_investment !== undefined
    ? surplus_after_investment
    : (monthlySurplus - monthly_investment)

  const equityPct = allocation ? Math.round(allocation.equity * 100) : 40
  const debtPct = 100 - equityPct
  const simCount = successful_simulations || Math.round((success_probability || 0.87) * 10000)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 sm:p-6 backdrop-blur-sm animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl border border-slate-800 bg-[#0d1322] shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4 bg-[#0a0f1d]">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-sm font-extrabold text-white border border-slate-700">
              {plan_id}
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">
                  Plan {plan_id} &middot; {label}
                </h3>
                {isSelected && (
                  <span className="rounded-full bg-indigo-500/15 px-2 py-0.5 text-[10px] font-semibold text-indigo-300 border border-indigo-500/30">
                    Currently Selected
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                {headline || 'Comprehensive Strategy Inspection'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:text-white hover:bg-slate-800/80 transition cursor-pointer"
            aria-label="Close modal"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Modal Body (Scrollable) */}
        <div className="overflow-y-auto p-6 space-y-6 text-xs text-slate-300">
          {/* Core Metric Highlights Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {/* Monthly Investment */}
            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Monthly Investment</p>
              <p className="mt-1 text-base font-extrabold text-white">{formatINR(monthly_investment)}</p>
              <p className="mt-0.5 text-[11px] text-slate-400">Committed monthly</p>
            </div>

            {/* Monthly Surplus Remaining */}
            <div className={`rounded-xl p-3 border ${
              surplusAfter < 0 ? 'bg-rose-950/20 border-rose-500/40' : 'bg-[#090e1a] border-slate-800'
            }`}>
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Monthly Surplus Left</p>
              <p className={`mt-1 text-base font-extrabold ${surplusAfter < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {surplusAfter < 0
                  ? `-₹${Math.abs(Math.round(surplusAfter)).toLocaleString('en-IN')}`
                  : `+${formatINR(surplusAfter)}`}
              </p>
              <p className={`mt-0.5 text-[11px] ${surplusAfter < 0 ? 'text-rose-400 font-semibold' : 'text-slate-400'}`}>
                {surplusAfter < 0 ? 'Deficit / Unaffordable' : 'Buffer remaining'}
              </p>
            </div>

            {/* Goal Success Probability */}
            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Success Probability</p>
              <p className="mt-1 text-base font-extrabold text-white">
                {Math.round((success_probability || 0) * 100)}%
              </p>
              <p className="mt-0.5 text-[11px] text-slate-400">{simCount.toLocaleString('en-IN')} runs</p>
            </div>

            {/* Expected Annual Return */}
            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Expected Return</p>
              <p className="mt-1 text-base font-extrabold text-white">
                {formatPercent(expected_annual_return)} p.a.
              </p>
              <p className="mt-0.5 text-[11px] text-slate-400">Compounded 5y</p>
            </div>
          </div>

          {/* Goal, Corpus & Asset Allocation Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Projected Corpus</p>
              <p className="mt-1 text-sm font-bold text-white">{formatINR(projected_corpus)}</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Target: {formatINR(goal_amount || 2500000)} in {years}y
              </p>
            </div>

            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Asset Allocation</p>
              <div className="mt-1 flex items-center justify-between text-xs font-semibold text-white">
                <span className="text-cyan-400">{equityPct}% Equity</span>
                <span className="text-indigo-400">{debtPct}% Debt</span>
              </div>
              <div className="w-full h-1.5 rounded-full overflow-hidden flex bg-slate-800 mt-1.5">
                <div className="bg-cyan-500 h-full" style={{ width: `${equityPct}%` }} />
                <div className="bg-indigo-500 h-full" style={{ width: `${debtPct}%` }} />
              </div>
            </div>

            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800 flex flex-col justify-between">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Status Verification</p>
              <div className="flex items-center justify-between text-xs font-semibold mt-1">
                <span className={feasible ? 'text-emerald-400' : 'text-rose-400'}>
                  {feasible ? '✓ Affordable' : '✕ Deficit'}
                </span>
                <span className={survives_stress ? 'text-emerald-400' : 'text-amber-400'}>
                  {survives_stress ? '✓ Survives Stress' : '⚠ Stress Vulnerable'}
                </span>
              </div>
              {exceeds_risk_ceiling && (
                <span className="text-[10px] text-rose-400 font-medium mt-1">
                  ⚠ Exceeds moderate risk ceiling
                </span>
              )}
            </div>
          </div>

          {/* Section 1: WHY THIS PLAN */}
          <div className="rounded-xl bg-slate-950/60 p-4 border border-slate-800/80 space-y-2">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-300">
              Why This Plan
            </h4>
            {headline && (
              <p className="font-semibold text-white text-xs">{headline}</p>
            )}
            <p className="text-xs text-slate-300 leading-relaxed">
              {body}
            </p>
          </div>

          {/* Section 2: TRADE-OFFS (Pros & Cons) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Pros */}
            <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-2">
              <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">
                Strengths & Benefits
              </p>
              {pros && pros.length > 0 ? (
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {pros.map((pro, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold">✓</span>
                      <span>{pro}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-400">Standard market return alignment.</p>
              )}
            </div>

            {/* Cons */}
            <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-2">
              <p className="text-[11px] font-bold uppercase tracking-wider text-rose-400">
                Trade-offs & Potential Risks
              </p>
              {cons && cons.length > 0 ? (
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {cons.map((con, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-rose-400 font-bold">✕</span>
                      <span>{con}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-400">Minimal structural trade-offs identified.</p>
              )}
            </div>
          </div>

          {/* Section 3: SIMULATION OUTCOMES */}
          <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-3">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-300">
              Simulation Outcomes (10,000 Monte Carlo Runs)
            </h4>
            <div className="grid grid-cols-3 gap-2.5 text-center">
              <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">10th Percentile (P10)</span>
                <p className="text-sm font-bold text-white mt-1">{formatINR(p10_corpus)}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">Adverse Market Case</p>
              </div>
              <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">Median (P50)</span>
                <p className="text-sm font-bold text-cyan-300 mt-1">{formatINR(median_corpus)}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">Expected Baseline</p>
              </div>
              <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">90th Percentile (P90)</span>
                <p className="text-sm font-bold text-emerald-400 mt-1">{formatINR(p90_corpus)}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">Favorable Growth</p>
              </div>
            </div>
          </div>

          {/* Section 4: STRESS TEST ANALYSIS */}
          <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-2">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-300">
              Adverse Stress Testing
            </h4>
            {!survives_stress && breaking_combo ? (
              <div className="rounded-lg bg-amber-950/20 p-3 border border-amber-500/30 text-xs text-amber-200 space-y-2">
                <div className="flex items-center gap-2 font-semibold text-amber-300">
                  <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>Breaking Shock Events Identified:</span>
                </div>
                <ul className="list-disc list-inside space-y-1 text-amber-200/90 pl-1">
                  {breaking_combo.map((event, idx) => (
                    <li key={idx}>
                      {event.label} &middot; <span className="font-mono text-amber-100">{formatINR(event.cash_impact)}</span> cash impact
                    </li>
                  ))}
                </ul>
                {shortfall_if_hit && (
                  <p className="text-xs font-semibold text-amber-300 pt-1.5 border-t border-amber-500/20">
                    Projected shortfall if shock hits: <strong className="text-white">{formatINR(shortfall_if_hit)}</strong>
                  </p>
                )}
              </div>
            ) : (
              <div className="rounded-lg bg-emerald-950/20 p-3 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
                <span className="font-bold text-emerald-400">✓</span>
                <span>Survives tested stress scenarios across 165 shock combinations with no projected cash shortfall.</span>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer with Action Buttons */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-800/80 px-6 py-4 bg-[#0a0f1d]">
          <div className="flex flex-wrap items-center gap-2">
            {onChallenge && (
              <button
                type="button"
                onClick={onChallenge}
                className="rounded-xl bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-slate-800 px-3 py-2 text-xs font-semibold transition cursor-pointer"
              >
                Challenge this plan &rarr;
              </button>
            )}

            {onWhatIf && (
              <button
                type="button"
                onClick={onWhatIf}
                className="rounded-xl bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-slate-800 px-3 py-2 text-xs font-semibold transition cursor-pointer"
              >
                What-If analysis &rarr;
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 px-4 py-2 text-xs font-semibold transition cursor-pointer"
            >
              Close
            </button>

            <button
              type="button"
              onClick={onSelect}
              className={`rounded-xl px-4 py-2 text-xs font-bold transition shadow-md cursor-pointer ${
                isSelected
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/25'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30'
              }`}
            >
              {isSelected ? '✓ Selected Strategy' : 'Select this plan'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
