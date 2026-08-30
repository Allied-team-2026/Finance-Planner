import { useState } from 'react'

export default function RiskMismatchAlert({ risk, mismatchNote, profile }) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!risk || !risk.mismatch) return null

  // Everything here comes from the backend. No default risk label and no default
  // confidence: inventing a risk category would be a made-up finding about a real
  // person, which is worse than an empty box.
  const confidencePct = risk.confidence == null ? null : Math.round(risk.confidence * 100)
  const statedRisk = risk.stated ?? '—'
  const revealedRisk = risk.revealed ?? '—'
  const riskCapacity = profile?.risk_capacity ?? '—'
  const capacityReasons = profile?.risk_capacity_reasons || []

  return (
    <section className="relative overflow-hidden rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-950/20 via-[#131c2e] to-[#0f172a] p-5 shadow-xl shadow-amber-950/20 backdrop-blur-md">
      {/* Decorative amber highlight bar */}
      <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-amber-400 to-amber-600" />

      <div className="flex flex-col gap-4">
        {/* Header Row */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <svg className="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-base font-bold tracking-tight text-white">
                  Risk profile mismatch detected
                </h3>
                <span className="rounded-full bg-amber-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-amber-300 border border-amber-500/30">
                  Model confidence: {confidencePct == null ? '—' : `${confidencePct}%`}
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Your stated risk preference differs from the risk indicated by your financial behaviour and capacity.
              </p>
            </div>
          </div>

          {/* Toggle Evidence Button */}
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800/90 hover:bg-slate-700/90 px-3 py-1.5 text-xs font-medium text-amber-200 border border-amber-500/25 transition cursor-pointer"
          >
            <span>{isExpanded ? 'Hide Evidence & Factors' : 'View Evidence & Factors'}</span>
            <svg
              className={`h-3.5 w-3.5 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>

        {/* 3-Dimensional Risk Relationship Flow: Stated -> Revealed -> Capacity */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
          {/* 1. Stated Risk */}
          <div className="rounded-xl bg-[#0a0f1d]/80 p-3.5 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Stated Risk
                </p>
                <span className="text-[10px] text-slate-400">Self-reported</span>
              </div>
              <p className="mt-1.5 text-lg font-bold capitalize text-white tracking-tight">
                {statedRisk}
              </p>
            </div>
            <p className="mt-2 text-[11px] text-slate-400 border-t border-slate-850 pt-1.5 leading-snug">
              What the customer states they are comfortable with.
            </p>
          </div>

          {/* 2. Revealed Risk */}
          <div className="rounded-xl bg-amber-950/20 p-3.5 border border-amber-500/30 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
                  Revealed Risk
                </p>
                <span className="text-[10px] text-amber-300 font-medium">Observed behavior</span>
              </div>
              <p className="mt-1.5 text-lg font-bold capitalize text-amber-300 tracking-tight">
                {revealedRisk}
              </p>
            </div>
            <p className="mt-2 text-[11px] text-amber-200/80 border-t border-amber-500/20 pt-1.5 leading-snug">
              What observed financial transaction behavior indicates.
            </p>
          </div>

          {/* 3. Risk Capacity */}
          <div className="rounded-xl bg-[#0a0f1d]/80 p-3.5 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Risk Capacity
                </p>
                <span className="text-[10px] text-slate-400">Financial capacity</span>
              </div>
              <p className="mt-1.5 text-lg font-bold capitalize text-white tracking-tight">
                {riskCapacity}
              </p>
            </div>
            <p className="mt-2 text-[11px] text-slate-400 border-t border-slate-850 pt-1.5 leading-snug">
              Ability to withstand financial loss based on financial situation.
            </p>
          </div>
        </div>

        {/* Neutral AI Synthesis Statement. The wording is the agent's, written
            for this customer. We do not supply a fallback story, because a story
            about panic selling that this customer never did is a false finding. */}
        {mismatchNote && (
          <div className="rounded-xl bg-slate-950/50 p-3 border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
            <p>
              <strong className="text-white">Observation: </strong>
              {mismatchNote}
            </p>
          </div>
        )}

        {/* Expandable Evidence & Risk Capacity Factors */}
        {isExpanded && (
          <div className="mt-1 pt-3 border-t border-slate-800/80 flex flex-col gap-4 animate-fadeIn">
            {/* Section 1: Behavioral Signals & Audit Trail */}
            {risk.evidence && risk.evidence.length > 0 && (
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2">
                  Observed Behavioral Evidence (Revealed Risk):
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {risk.evidence.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 rounded-lg bg-slate-900/90 p-2.5 border border-slate-800 text-xs text-slate-300">
                      <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-400">
                        {idx + 1}
                      </span>
                      <span className="leading-snug">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Section 2: Behavioral Feature Metrics */}
            {risk.features_used && (
              <div className="flex flex-wrap gap-2 text-[11px] text-slate-400">
                <span className="rounded bg-slate-900/90 px-2.5 py-1 border border-slate-800">
                  Panic Sell Count: <strong className="text-white">{risk.features_used.panic_sell_count}</strong>
                </span>
                <span className="rounded bg-slate-900/90 px-2.5 py-1 border border-slate-800">
                  Avg Days to Exit: <strong className="text-white">{risk.features_used.avg_days_to_exit_after_drop} days</strong>
                </span>
                <span className="rounded bg-slate-900/90 px-2.5 py-1 border border-slate-800">
                  Expense Volatility: <strong className="text-white">{Math.round(risk.features_used.expense_volatility * 100)}%</strong>
                </span>
                <span className="rounded bg-slate-900/90 px-2.5 py-1 border border-slate-800">
                  Budget Overshoot Rate: <strong className="text-white">{Math.round(risk.features_used.budget_overshoot_rate * 100)}%</strong>
                </span>
              </div>
            )}

            {/* Section 3: Risk Capacity Reasons */}
            {capacityReasons.length > 0 && (
              <div className="pt-2 border-t border-slate-800/80">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Financial Risk Capacity Factors (Ability to Withstand Loss):
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {capacityReasons.map((reason, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 rounded-lg bg-slate-900/90 p-2.5 border border-slate-800 text-xs text-slate-300">
                      <span className="text-indigo-400 font-bold text-xs mt-0.5">•</span>
                      <span className="leading-snug">{reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
