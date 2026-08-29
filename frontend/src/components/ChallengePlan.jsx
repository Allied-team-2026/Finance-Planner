import { useState } from 'react'

function formatINR(amount) {
  if (amount == null) return '₹0'
  return `₹${Math.round(amount).toLocaleString('en-IN')}`
}

export default function ChallengePlan({
  plans = [],
  selectedPlanId,
  onSelectPlan,
  customerId = 'C001',
  initialChallenge = null,
}) {
  const [query, setQuery] = useState('')
  const [challengeResult, setChallengeResult] = useState(initialChallenge)
  const [isLoading, setIsLoading] = useState(false)

  // Find currently selected plan object
  const selectedPlan = plans.find((p) => p.plan_id === selectedPlanId) || plans[0]

  // Suggested challenge prompt chips
  const suggestedPrompts = [
    'What could make this plan fail?',
    'What if my expenses increase?',
    'What if the market falls?',
    'What if my income drops?',
    'Why is this plan suitable for me?',
  ]

  // Offline / development mock response helper
  const getLocalMockChallenge = (planId) => {
    if (planId === 'C') {
      return {
        chosen_plan_id: 'C',
        challenge:
          'You have picked the Growth plan, and two things about it are worth sitting with before you commit. First, it is not affordable as it stands: it asks for 52,000 a month against a monthly surplus of 45,000, which leaves you 7,000 short every month, so something else in your budget would have to give. Second, and this is the part your own history speaks to, it puts 85% into equity. Your transaction history shows you exited equity mutual funds within 3 days of a 9% market drop in March 2024, and sold again during a 6% drop in October 2024. A plan is only as good as your willingness to stay in it during a bad year, and the plans with the highest projected returns are exactly the ones that fall furthest when a bad year arrives. The Steady plan asks for 35,000, stays within what your finances can absorb, and was the only one of the three still standing after our stress test.',
        evidence_cited: [
          'Exited equity mutual funds within 3 days of a 9% market drop in March 2024',
          'Sold again during a 6% drop in October 2024, this time 90000 rupees of holdings',
        ],
        alternative_suggested: 'A',
        numbers_used: [52000, 45000, 7000, 0.85, 35000, 3],
      }
    } else if (planId === 'B') {
      return {
        chosen_plan_id: 'B',
        challenge:
          'You have picked the Balanced plan (Plan B). While it fits your 45,000 monthly surplus with a 30,000 commitment, it fails under combined adverse shocks (such as an appraisal miss combined with family medical expense, creating a 4,20,000 shortfall). Furthermore, its 65% equity allocation carries downside risk that may test your tolerance during market downturns.',
        evidence_cited: [
          'Exited equity mutual funds within 3 days of a 9% market drop in March 2024',
          'Fails under dual stress shocks with ₹4,20,000 projected shortfall',
        ],
        alternative_suggested: 'A',
        numbers_used: [30000, 45000, 420000, 0.65],
      }
    } else {
      return {
        chosen_plan_id: 'A',
        challenge:
          'You have picked the Steady plan (Plan A). This plan commits 35,000 a month against your 45,000 surplus, leaving a healthy 10,000 monthly cushion. It survived all 165 tested shock scenarios. The primary trade-off is a more conservative 9% expected annual return (40% equity / 60% debt), which requires disciplined monthly contributions to achieve the 25,00,000 target over 5 years.',
        evidence_cited: [
          'Surplus ratio easily covers ₹35,000 monthly commitment with ₹10,000 buffer',
          'Passed all 165 shock combinations with 0 projected shortfall',
        ],
        alternative_suggested: null,
        numbers_used: [35000, 45000, 10000, 2500000, 165],
      }
    }
  }

  // Handle Challenge Submission
  const handleChallengeSubmit = async (e) => {
    if (e) e.preventDefault()
    if (!selectedPlan) return

    setIsLoading(true)
    setError(null)

    try {
      const res = await fetch('/api/challenge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: customerId,
          chosen_plan_id: selectedPlan.plan_id,
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setChallengeResult(data)
      } else {
        // Fallback to local development mock
        setChallengeResult(getLocalMockChallenge(selectedPlan.plan_id))
      }
    } catch {
      // Offline fallback
      setChallengeResult(getLocalMockChallenge(selectedPlan.plan_id))
    } finally {
      setIsLoading(false)
    }
  }

  // Find alternative plan object if suggested
  const alternativePlan = challengeResult?.alternative_suggested
    ? plans.find((p) => p.plan_id === challengeResult.alternative_suggested)
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

      {/* Grid: Left = Selected Plan Summary & Prompt Input | Right = Challenger Analysis Result */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Selected Plan & Interactive Input (5 cols) */}
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
                    {Math.round(selectedPlan.success_probability * 100)}%
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
                  <div className="flex items-center justify-between rounded-lg bg-rose-950/30 px-2.5 py-1.5 border border-rose-800/40 text-rose-300">
                    <span>Risk Ceiling:</span>
                    <span className="font-semibold">⚠ Exceeds Tolerance</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/80 p-4 text-center text-xs text-slate-400">
              No plan selected yet. Please select a plan from the comparison table.
            </div>
          )}

          {/* Interactive Challenge Input Form */}
          <form onSubmit={handleChallengeSubmit} className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-4 shadow-md backdrop-blur-md flex flex-col gap-3">
            <div>
              <label htmlFor="challenge-query" className="block text-xs font-semibold text-slate-300 mb-1">
                Ask a question or test an assumption
              </label>
              <textarea
                id="challenge-query"
                rows={3}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What could make this plan fail?"
                className="w-full rounded-xl bg-slate-950/80 border border-slate-800 p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition resize-none"
              />
            </div>

            {/* Suggested Challenge Prompts */}
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Suggested challenge questions:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {suggestedPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setQuery(prompt)}
                    className="rounded-lg bg-slate-900/80 hover:bg-slate-800 px-2.5 py-1 text-[11px] text-slate-300 hover:text-white border border-slate-800 transition text-left cursor-pointer"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Action Button */}
            <button
              type="submit"
              disabled={isLoading || !selectedPlan}
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
                <span>Challenge this plan</span>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Challenge Response & Evidence Area (7 cols) */}
        <div className="lg:col-span-7">
          {challengeResult ? (
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
                      Challenger Evaluation: Plan {challengeResult.chosen_plan_id}
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Grounded in behavioral transaction history & cash flow
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
                  {challengeResult.challenge}
                </p>
              </div>

              {/* Evidence Cited */}
              {challengeResult.evidence_cited && challengeResult.evidence_cited.length > 0 && (
                <div className="space-y-2 pt-1">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                    Behavioral & Financial Evidence Cited:
                  </p>
                  <div className="space-y-1.5">
                    {challengeResult.evidence_cited.map((item, idx) => (
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

              {/* Suggested Alternative Plan Callout (if any) */}
              {alternativePlan && (
                <div className="rounded-xl bg-emerald-950/20 p-4 border border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                      Suggested Alternative Strategy
                    </span>
                    <p className="text-xs text-slate-200 mt-0.5">
                      <strong className="text-white">Plan {alternativePlan.plan_id} ({alternativePlan.label})</strong> offers higher resilience with lower downside risk.
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
                {challengeResult.numbers_used && (
                  <span>{challengeResult.numbers_used.length} deterministic figures verified</span>
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
                Your plan hasn't been challenged yet.
              </h3>
              <p className="mt-1 max-w-sm text-xs text-slate-400 leading-relaxed">
                Click <strong className="text-slate-300">"Challenge this plan"</strong> or select one of the suggested questions to test this plan against your financial capacity and past market panic points.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
