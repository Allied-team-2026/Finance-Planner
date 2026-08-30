import { useState } from 'react'

function formatINR(amount) {
  if (amount == null || isNaN(amount)) return '—'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

function formatPercent(decimal) {
  if (decimal == null || isNaN(decimal)) return '—'
  return `${Math.round(Number(decimal) * 100)}%`
}

export default function SelectedPlanSummary({
  plans = [],
  selectedPlanId = 'A',
  goals = [],
  onStartNewAnalysis,
}) {
  const [savedTime, setSavedTime] = useState(null)

  // Find currently selected plan object dynamically
  const selectedPlan = plans.find((p) => p.plan_id === selectedPlanId) || plans[0]

  // Identify targeted primary goal
  const primaryGoal = goals && goals.length > 0 ? goals[0] : null

  if (!selectedPlan) return null

  // Read, never derive. The backend already worked all of this out.
  const equityPct = selectedPlan.allocation ? Math.round(selectedPlan.allocation.equity * 100) : null
  const debtPct = equityPct == null ? null : 100 - equityPct
  const surplusAfter = selectedPlan.surplus_after_investment

  // Dynamic derivation of evidence points for "Why this strategy?"
  const evidencePoints = []

  if (selectedPlan.feasible) {
    evidencePoints.push({
      status: 'positive',
      text: `Fits within your monthly surplus and leaves ${formatINR(surplusAfter)} spare each month`,
    })
  } else {
    evidencePoints.push({
      status: 'negative',
      text: `Costs ${formatINR(surplusAfter == null ? null : Math.abs(surplusAfter))} a month more than your surplus allows`,
    })
  }

  if (selectedPlan.survives_stress) {
    evidencePoints.push({
      status: 'positive',
      text: 'Survives every tested combination of adverse shocks without a shortfall',
    })
  } else {
    evidencePoints.push({
      status: 'warning',
      text: selectedPlan.breaking_combo
        ? `Fails under ${selectedPlan.breaking_combo}`
        : 'Fails under combined adverse shocks',
    })
  }

  if (selectedPlan.success_probability != null) {
    evidencePoints.push({
      status: 'positive',
      text: `${formatPercent(selectedPlan.success_probability)} of simulations reach the goal`,
    })
  }

  if (selectedPlan.exceeds_risk_ceiling) {
    evidencePoints.push({
      status: 'negative',
      text: `Holds more equity than your risk profile supports (${equityPct == null ? '—' : equityPct + '%'} equity)`,
    })
  } else if (equityPct != null) {
    evidencePoints.push({
      status: 'neutral',
      text: `Allocation matches your risk profile (${equityPct}% equity / ${debtPct}% debt)`,
    })
  }

  // Handle Session-Scoped Save Action
  const handleSaveStrategy = () => {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    setSavedTime(timeStr)
  }

  return (
    <section id="summary-section" className="flex flex-col gap-6 scroll-mt-8">
      {/* 1. Decision Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-400 border border-emerald-500/20">
            Final Decision Summary
          </span>
          <span className="text-xs text-slate-400">
            Session strategy overview
          </span>
        </div>
        <h2 className="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Your selected strategy
        </h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-400 leading-relaxed">
          Review the strategy, assumptions, and trade-offs before saving it.
        </p>
      </div>

      {/* 2. Main Selected Plan Overview Card */}
      <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-6 sm:p-7 shadow-xl backdrop-blur-md flex flex-col gap-6">
        {/* Top Strategy Identity Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
          <div className="flex items-center gap-3.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 text-sm font-extrabold text-white border border-slate-700">
              {selectedPlan.plan_id}
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-white">
                  Plan {selectedPlan.plan_id} &middot; {selectedPlan.label}
                </h3>
                <span className="rounded-full bg-indigo-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-300 border border-indigo-500/30">
                  Selected
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Targeting: {primaryGoal ? primaryGoal.name.replace(/_/g, ' ') : '—'} ({formatINR(selectedPlan.goal_amount)}
                {selectedPlan.years == null ? '' : ` in ${selectedPlan.years} years`})
              </p>
            </div>
          </div>

          {/* Save Action & Feedback */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            {savedTime ? (
              <div className="inline-flex items-center gap-2 rounded-xl bg-emerald-950/30 px-4 py-2 border border-emerald-500/40 text-xs font-semibold text-emerald-300">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Strategy saved for this session ({savedTime})</span>
              </div>
            ) : (
              <button
                type="button"
                onClick={handleSaveStrategy}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-600/25 transition cursor-pointer"
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                  <polyline points="17 21 17 13 7 13 7 21" />
                  <polyline points="7 3 7 8 15 8" />
                </svg>
                <span>Save this strategy</span>
              </button>
            )}
          </div>
        </div>

        {/* Core Financial Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
          {/* Monthly Investment */}
          <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Monthly Commitment</p>
            <p className="mt-1 text-base font-extrabold text-white">{formatINR(selectedPlan.monthly_investment)}</p>
            <p className="mt-0.5 text-[11px] text-slate-400">Committed monthly</p>
          </div>

          {/* Monthly Surplus Remaining */}
          <div className={`rounded-xl p-3 border ${
            surplusAfter != null && surplusAfter < 0 ? 'bg-rose-950/20 border-rose-500/30' : 'bg-[#090e1a] border-slate-800'
          }`}>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Surplus Left</p>
            <p className={`mt-1 text-base font-extrabold ${
              surplusAfter == null ? 'text-slate-400' : surplusAfter < 0 ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              {surplusAfter == null
                ? '—'
                : surplusAfter < 0
                ? `-₹${Math.abs(Math.round(surplusAfter)).toLocaleString('en-IN')}`
                : `+${formatINR(surplusAfter)}`}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">
              {surplusAfter == null ? 'Not reported' : surplusAfter < 0 ? 'Monthly Deficit' : 'Buffer Remaining'}
            </p>
          </div>

          {/* Success Probability */}
          <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Goal Success</p>
            <p className="mt-1 text-base font-extrabold text-white">
              {formatPercent(selectedPlan.success_probability)}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">
              {selectedPlan.successful_simulations == null
                ? 'In simulation'
                : `${selectedPlan.successful_simulations.toLocaleString('en-IN')} runs reached the goal`}
            </p>
          </div>

          {/* Expected Return */}
          <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Expected Return</p>
            <p className="mt-1 text-base font-extrabold text-white">
              {formatPercent(selectedPlan.expected_annual_return)} p.a.
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">
              {selectedPlan.years == null ? 'Compounded' : `Compounded ${selectedPlan.years}y`}
            </p>
          </div>

          {/* Projected Corpus */}
          <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Projected Corpus</p>
            <p className="mt-1 text-base font-extrabold text-white">{formatINR(selectedPlan.projected_corpus)}</p>
            <p className="mt-0.5 text-[11px] text-slate-400">Target: {formatINR(selectedPlan.goal_amount)}</p>
          </div>

          {/* Asset Allocation */}
          <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800 flex flex-col justify-between">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Allocation</p>
            <div>
              <p className="text-xs font-bold text-white">
                <span className="text-cyan-400">{equityPct == null ? '—' : `${equityPct}% Eq`}</span> &middot;{' '}
                <span className="text-indigo-400">{debtPct == null ? '—' : `${debtPct}% Debt`}</span>
              </p>
              <div className="w-full h-1.5 rounded-full overflow-hidden flex bg-slate-800 mt-1.5">
                <div className="bg-cyan-500 h-full" style={{ width: `${equityPct ?? 0}%` }} />
                <div className="bg-indigo-500 h-full" style={{ width: `${debtPct ?? 0}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* 3. "Why this strategy?" Section */}
        <div className="rounded-xl bg-slate-950/60 p-4 sm:p-5 border border-slate-800/80 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Why this strategy?
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {evidencePoints.map((pt, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 rounded-lg bg-[#090e1a] p-2.5 border border-slate-800 text-xs text-slate-300"
              >
                <span className={`font-bold text-xs ${
                  pt.status === 'positive'
                    ? 'text-emerald-400'
                    : pt.status === 'negative'
                    ? 'text-rose-400'
                    : pt.status === 'warning'
                    ? 'text-amber-400'
                    : 'text-cyan-400'
                }`}>
                  {pt.status === 'positive' ? '✓' : pt.status === 'negative' ? '✕' : '•'}
                </span>
                <span className="leading-snug">{pt.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 4. "Trade-offs to understand" Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Strengths / Pros */}
          <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-2.5">
            <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">
              Key Strengths
            </p>
            {selectedPlan.pros && selectedPlan.pros.length > 0 ? (
              <ul className="space-y-1.5 text-xs text-slate-300">
                {selectedPlan.pros.map((pro, idx) => (
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

          {/* Trade-offs & Risks / Cons */}
          <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-2.5">
            <p className="text-[11px] font-bold uppercase tracking-wider text-rose-400">
              Trade-offs to understand
            </p>
            {selectedPlan.cons && selectedPlan.cons.length > 0 ? (
              <ul className="space-y-1.5 text-xs text-slate-300">
                {selectedPlan.cons.map((con, idx) => (
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

        {/* Detailed Narrative Body */}
        {selectedPlan.body && (
          <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 text-xs text-slate-300 leading-relaxed">
            {selectedPlan.headline && (
              <p className="font-semibold text-white mb-1">{selectedPlan.headline}</p>
            )}
            <p>{selectedPlan.body}</p>
          </div>
        )}

        {/* 5. Goal Alignment Row */}
        {primaryGoal && (
          <div className="rounded-xl bg-slate-950/60 p-4 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold text-xs">
                #{primaryGoal.priority || 1}
              </span>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Targeted Primary Goal
                </span>
                <p className="text-sm font-bold text-white capitalize">
                  {primaryGoal.displayName || primaryGoal.name.replace(/_/g, ' ')}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-slate-300">
              <span>Target: <strong className="text-white">{formatINR(primaryGoal.target_amount)}</strong></span>
              <span>&middot;</span>
              <span>Horizon: <strong className="text-white">{primaryGoal.years} Years</strong></span>
            </div>
          </div>
        )}

        {/* 6. Navigation Actions Strip */}
        <div className="border-t border-slate-800/80 pt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <a
              href="#plans-section"
              className="rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 transition cursor-pointer"
            >
              &larr; Back to plans
            </a>
            <a
              href="#challenge-section"
              className="rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3.5 py-2 text-xs font-semibold text-indigo-300 transition cursor-pointer"
            >
              Challenge this strategy &rarr;
            </a>
            <a
              href="#whatif-section"
              className="rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3.5 py-2 text-xs font-semibold text-cyan-300 transition cursor-pointer"
            >
              What-If analysis &rarr;
            </a>
          </div>

          {onStartNewAnalysis && (
            <button
              type="button"
              onClick={onStartNewAnalysis}
              className="rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-750 px-3.5 py-2 text-xs font-semibold text-slate-300 transition cursor-pointer"
            >
              + Start a new analysis
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
