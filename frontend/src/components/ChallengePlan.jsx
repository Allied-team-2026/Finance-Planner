import { useState } from 'react'
import { fetchChallenge } from '../services/api'

function formatINR(amount) {
  if (amount == null || isNaN(amount)) return '—'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

export default function ChallengePlan({
  plans = [],
  selectedPlanId,
  onSelectPlan,
  customerId,
  initialChallenge = null,
}) {
  const [challengeResult, setChallengeResult] = useState(initialChallenge)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Find currently selected plan object
  const selectedPlan = plans.find((p) => p.plan_id === selectedPlanId) || plans[0]

  // A challenge belongs to the plan it was run against. If the pick changes
  // afterwards - including by clicking "Switch to Plan X" in this very panel -
  // the old challenge is not about the new plan, so it is not shown. Deriving
  // this from the result itself means there is no second copy of the selection
  // to keep in sync.
  const staleChallenge =
    challengeResult != null &&
    selectedPlan != null &&
    challengeResult.chosen_plan_id !== selectedPlan.plan_id
  const activeChallenge = staleChallenge ? null : challengeResult

  // Ask the backend to challenge the selected plan. There is no local fallback
  // response: a canned challenge would read exactly like a real one, and the
  // whole point of this screen is that every claim is traceable to the engines.
  const handleChallengeSubmit = async (e) => {
    if (e) e.preventDefault()
    if (!selectedPlan || !customerId) return

    setIsLoading(true)
    setError(null)

    try {
      const data = await fetchChallenge(customerId, selectedPlan.plan_id)
      setChallengeResult(data)
    } catch (err) {
      setChallengeResult(null)
      setError(err.message || 'Unable to reach the backend to challenge this plan.')
    } finally {
      setIsLoading(false)
    }
  }

  // Find alternative plan object if suggested. The agent returns a plan letter,
  // so anything that does not match a real plan is ignored rather than shown.
  const alternativePlan = activeChallenge?.alternative_suggested
    ? plans.find((p) => p.plan_id === activeChallenge.alternative_suggested)
    : null

  return (
    <section id="challenge-section" className="flex flex-col gap-6 scroll-mt-8">
      {/* Section Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-indigo-500/10 px-2.5 py-1 text-[11px] font-semibold text-indigo-400 border border-indigo-500/20">
            Challenger Agent
          </span>
          <span className="text-xs text-slate-400">
            Pre-commitment assumption testing
          </span>
        </div>
        <h2 className="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Challenge your plan
        </h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-400 leading-relaxed">
          Before you commit, test the assumptions behind your choice.
        </p>
      </div>

      {/* Grid: Left = Selected Plan Summary & Run Control | Right = Challenger Analysis Result */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Selected Plan & Run Control (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          {/* Selected Plan Summary Card */}
          {selectedPlan ? (
            <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-4 shadow-md backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-3">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Currently Selected Plan
                  </span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="flex h-5 w-5 items-center justify-center rounded bg-slate-800 text-xs font-bold text-white border border-slate-700">
                      {selectedPlan.plan_id}
                    </span>
                    <span className="text-base font-bold text-white">
                      {selectedPlan.label}
                    </span>
                  </div>
                </div>
                <span className="rounded-full bg-indigo-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-300 border border-indigo-500/30">
                  Ready to Challenge
                </span>
              </div>

              {/* Core Attributes Summary */}
              <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                <div className="rounded-xl bg-[#090e1a] p-2.5 border border-slate-800">
                  <p className="text-[10px] text-slate-400">Monthly investment</p>
                  <p className="mt-0.5 text-sm font-bold text-white">
                    {formatINR(selectedPlan.monthly_investment)}
                  </p>
                </div>
                <div className="rounded-xl bg-[#090e1a] p-2.5 border border-slate-800">
                  <p className="text-[10px] text-slate-400">Success probability</p>
                  <p className="mt-0.5 text-sm font-bold text-white">
                    {selectedPlan.success_probability == null
                      ? '—'
                      : `${Math.round(selectedPlan.success_probability * 100)}%`}
                  </p>
                </div>
              </div>

              {/* Status Verification Badges */}
              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between rounded-lg bg-slate-950/60 px-2.5 py-1.5 border border-slate-800">
                  <span className="text-slate-400">Affordability:</span>
                  <span className={`font-semibold ${selectedPlan.feasible ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {selectedPlan.feasible ? '✓ Affordable within surplus' : '✕ Not Affordable'}
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-slate-950/60 px-2.5 py-1.5 border border-slate-800">
                  <span className="text-slate-400">Stress-Test:</span>
                  <span className={`font-semibold ${selectedPlan.survives_stress ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {selectedPlan.survives_stress ? '✓ Survives tested shocks' : '⚠ Fails under stress'}
                  </span>
                </div>
                {selectedPlan.exceeds_risk_ceiling && (
                  <div className="flex items-center justify-between rounded-lg bg-amber-950/30 px-2.5 py-1.5 border border-amber-800/40 text-amber-300">
                    <span>Risk Ceiling:</span>
                    <span className="font-semibold">⚠ Above your risk level</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/80 p-4 text-center text-xs text-slate-400">
              No plan selected yet. Please select a plan from the comparison table.
            </div>
          )}

          {/* Run Control: what the challenger does, and the button that runs it */}
          <form onSubmit={handleChallengeSubmit} className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-4 shadow-md backdrop-blur-md flex flex-col gap-3">
            <div>
              <p className="text-xs font-semibold text-slate-300">
                What the challenger tests
              </p>
              <p className="mt-1 text-[11px] text-slate-400 leading-relaxed">
                It argues against the plan you picked, using only your own numbers.
                It checks whether the monthly commitment fits your surplus, whether
                the plan survived the shock combinations, whether the equity share
                matches how you have actually behaved in a falling market, and what
                the plan gives up to reach your goal.
              </p>
            </div>

            <ul className="space-y-1 text-[11px] text-slate-400">
              <li className="flex items-start gap-2">
                <span className="text-indigo-400">•</span>
                <span>It never invents a number or a probability.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400">•</span>
                <span>It never sees your name, customer id, or transactions.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400">•</span>
                <span>It may suggest a different plan, but it will not rank all three.</span>
              </li>
            </ul>

            {error && (
              <div className="mt-1 text-xs text-rose-400 bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !selectedPlan || !customerId}
              className="mt-1 w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-semibold text-white shadow-md shadow-indigo-600/30 transition flex items-center justify-center gap-2 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Challenging Plan {selectedPlan?.plan_id}...</span>
                </>
              ) : (
                <span>
                  {selectedPlan ? `Challenge Plan ${selectedPlan.plan_id}` : 'Challenge this plan'}
                </span>
              )}
            </button>

            {!customerId && (
              <p className="text-[11px] text-slate-500 text-center">
                Available once a customer analysis is loaded.
              </p>
            )}
          </form>
        </div>

        {/* Right Column: Challenge Response & Evidence Area (7 cols) */}
        <div className="lg:col-span-7">
          {activeChallenge ? (
            <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-5 shadow-lg backdrop-blur-md flex flex-col gap-4 animate-fadeIn">
              {/* Header Badge */}
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      Challenger Evaluation
                      {activeChallenge.chosen_plan_id
                        ? `: Plan ${activeChallenge.chosen_plan_id}`
                        : ''}
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Grounded in your cash flow and your past market behaviour
                    </p>
                  </div>
                </div>

                <span className="rounded-full bg-slate-900 px-2.5 py-1 text-[11px] font-mono text-slate-400 border border-slate-800">
                  Audited Response
                </span>
              </div>

              {/* Challenge Narrative Body */}
              <div className="rounded-xl bg-slate-950/70 p-4 border border-slate-800/80">
                <p className="text-xs text-slate-200 leading-relaxed">
                  {activeChallenge.challenge}
                </p>
              </div>

              {/* Evidence Cited */}
              {activeChallenge.evidence_cited && activeChallenge.evidence_cited.length > 0 && (
                <div className="space-y-2 pt-1">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                    Behavioral & Financial Evidence Cited:
                  </p>
                  <div className="space-y-1.5">
                    {activeChallenge.evidence_cited.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2.5 rounded-lg bg-[#090e1a] p-2.5 border border-slate-800 text-xs text-slate-300"
                      >
                        <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-400">
                          {idx + 1}
                        </span>
                        <span className="leading-snug">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested Alternative Plan Callout (if any). The reason names the
                  alternative's own flags, so it cannot praise a plan that is worse. */}
              {alternativePlan && (
                <div className="rounded-xl bg-emerald-950/20 p-4 border border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                      Suggested Alternative Strategy
                    </span>
                    <p className="text-xs text-slate-200 mt-0.5">
                      <strong className="text-white">
                        Plan {alternativePlan.plan_id} ({alternativePlan.label})
                      </strong>{' '}
                      at {formatINR(alternativePlan.monthly_investment)} a month
                      {alternativePlan.feasible ? ', fits your surplus' : ''}
                      {alternativePlan.survives_stress ? ' and survives the tested shocks' : ''}
                      .
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onSelectPlan && onSelectPlan(alternativePlan.plan_id)}
                    className="shrink-0 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-3.5 py-2 text-xs font-semibold text-white shadow-md transition cursor-pointer"
                  >
                    Switch to Plan {alternativePlan.plan_id}
                  </button>
                </div>
              )}

              {/* Trust Footer */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  No fabricated numbers or probabilities
                </span>
                {activeChallenge.numbers_used && (
                  <span>
                    {activeChallenge.numbers_used.length} figures traced back to engine output
                  </span>
                )}
              </div>
            </div>
          ) : (
            /* Empty State */
            <div className="h-full min-h-[320px] rounded-2xl border border-dashed border-slate-800 bg-[#0d1322]/40 p-8 flex flex-col items-center justify-center text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-slate-400 border border-slate-800 mb-3">
                <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <path d="M9 12h6" />
                  <path d="M12 9v6" />
                </svg>
              </div>
              <h3 className="text-sm font-bold text-slate-200">
                {staleChallenge
                  ? `You changed your pick to Plan ${selectedPlan?.plan_id}.`
                  : "Your plan hasn't been challenged yet."}
              </h3>
              <p className="mt-1 max-w-sm text-xs text-slate-400 leading-relaxed">
                {staleChallenge ? (
                  <>
                    The earlier challenge argued against Plan{' '}
                    {challengeResult.chosen_plan_id}, so it does not apply here.
                    Run it again to challenge Plan {selectedPlan?.plan_id}.
                  </>
                ) : (
                  <>
                    Click{' '}
                    <strong className="text-slate-300">
                      {selectedPlan ? `"Challenge Plan ${selectedPlan.plan_id}"` : '"Challenge this plan"'}
                    </strong>{' '}
                    to argue against your own pick, using your financial capacity and
                    your past reaction to market falls.
                  </>
                )}
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
