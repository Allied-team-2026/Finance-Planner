import { useState } from 'react'
import { fetchWhatIf } from '../services/api'

function formatINR(amount) {
  if (amount == null || isNaN(amount)) return '₹0'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

export default function WhatIfAnalysis({
  plans = [],
  selectedPlanId = 'A',
  monthlySurplus = 45000,
  customerId = 'C001',
}) {
  const [extraSavings, setExtraSavings] = useState(10000)
  const [scenarioResult, setScenarioResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Current selected plan from baseline
  const selectedPlan = plans.find((p) => p.plan_id === selectedPlanId) || plans[0]

  const quickSelectAmounts = [5000, 10000, 20000, 30000]

  // Handle running what-if analysis
  const handleRunScenario = async (e) => {
    if (e) e.preventDefault()
    if (!selectedPlan) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetchWhatIf(customerId, extraSavings)
      if (response && response.plans) {
        setScenarioResult(response)
      } else {
        setError("We couldn't run this scenario right now.")
      }
    } catch {
      setError("We couldn't run this scenario right now.")
    } finally {
      setIsLoading(false)
    }
  }

  // Handle resetting scenario back to edit mode
  const handleAdjustScenario = () => {
    setScenarioResult(null)
    setError(null)
  }

  // Find scenario plan from returned payload
  const scenarioPlan = scenarioResult?.plans?.find((p) => p.plan_id === selectedPlan?.plan_id) || selectedPlan
  const scenarioSurplus = scenarioResult?.profile?.monthly_surplus || monthlySurplus + extraSavings
  const baselineSurplusAfter = selectedPlan
    ? (selectedPlan.surplus_after_investment !== undefined
        ? selectedPlan.surplus_after_investment
        : monthlySurplus - selectedPlan.monthly_investment)
    : 0
  const scenarioSurplusAfter = scenarioPlan
    ? (scenarioPlan.surplus_after_investment !== undefined
        ? scenarioPlan.surplus_after_investment
        : scenarioSurplus - scenarioPlan.monthly_investment)
    : 0

  return (
    <section id="whatif-section" className="flex flex-col gap-6 scroll-mt-8">
      {/* 1. Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-cyan-500/10 px-2.5 py-1 text-[11px] font-semibold text-cyan-400 border border-cyan-500/20">
            Scenario Simulator
          </span>
          <span className="text-xs text-slate-400">
            Real-time cash flow sensitivity testing
          </span>
        </div>
        <h2 className="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          What if your situation changes?
        </h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-400 leading-relaxed">
          Test how your selected strategy responds to changes in your financial situation.
        </p>
      </div>

      {/* 2. Selected Plan Summary Card */}
      {selectedPlan ? (
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-5 shadow-md backdrop-blur-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3 mb-4">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-800 text-xs font-bold text-white border border-slate-700">
                {selectedPlan.plan_id}
              </span>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Selected Baseline Plan
                </p>
                <h3 className="text-base font-bold text-white">
                  Plan {selectedPlan.plan_id} &middot; {selectedPlan.label}
                </h3>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-300">
                Baseline Surplus:{' '}
                <strong className="text-emerald-400">{formatINR(monthlySurplus)} / mo</strong>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Monthly Investment</p>
              <p className="mt-1 text-sm font-bold text-white">{formatINR(selectedPlan.monthly_investment)}</p>
            </div>

            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Success Probability</p>
              <p className="mt-1 text-sm font-bold text-white">
                {Math.round(selectedPlan.success_probability * 100)}%
              </p>
            </div>

            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Affordability</p>
              <p className={`mt-1 text-sm font-bold ${selectedPlan.feasible ? 'text-emerald-400' : 'text-rose-400'}`}>
                {selectedPlan.feasible ? '✓ Affordable' : '✕ Not Affordable'}
              </p>
            </div>

            <div className="rounded-xl bg-[#090e1a] p-3 border border-slate-800">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Stress Resilience</p>
              <p className={`mt-1 text-sm font-bold ${selectedPlan.survives_stress ? 'text-emerald-400' : 'text-amber-400'}`}>
                {selectedPlan.survives_stress ? '✓ Survives Shocks' : '⚠ Fails Under Stress'}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/80 p-6 text-center text-xs text-slate-400">
          No plan selected. Please select a plan from the comparison table above.
        </div>
      )}

      {/* 3. Scenario Controller & Interactive Execution */}
      {!scenarioResult ? (
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/90 p-6 shadow-md backdrop-blur-md flex flex-col gap-5">
          <div>
            <label htmlFor="extra-savings-slider" className="block text-xs font-semibold text-white mb-1">
              Additional monthly savings (extra cash flow)
            </label>
            <p className="text-xs text-slate-400">
              Simulate an increase in salary, discretionary budget cut, or loan payoff that expands your monthly surplus.
            </p>
          </div>

          {/* Quick Select Shortcut Chips */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold text-slate-400 mr-1">Quick Select:</span>
            {quickSelectAmounts.map((amt) => (
              <button
                key={amt}
                type="button"
                onClick={() => setExtraSavings(amt)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold border transition cursor-pointer ${
                  extraSavings === amt
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 ring-1 ring-cyan-500'
                    : 'bg-slate-900/80 text-slate-300 hover:text-white border-slate-800 hover:border-slate-700'
                }`}
              >
                +{formatINR(amt)} / mo
              </button>
            ))}
          </div>

          {/* Interactive Range Slider */}
          <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Simulated Extra Savings:</span>
              <span className="text-base font-extrabold text-cyan-400">
                +{formatINR(extraSavings)} / month
              </span>
            </div>

            <input
              id="extra-savings-slider"
              type="range"
              min="0"
              max="50000"
              step="1000"
              value={extraSavings}
              onChange={(e) => setExtraSavings(Number(e.target.value))}
              className="w-full accent-cyan-500 cursor-pointer"
            />

            <div className="flex justify-between text-[11px] text-slate-400">
              <span>₹0</span>
              <span>₹25,000</span>
              <span>₹50,000</span>
            </div>
          </div>

          {/* Projected Total Monthly Surplus Indicator */}
          <div className="flex items-center justify-between text-xs rounded-xl bg-slate-950/60 p-3.5 border border-slate-800">
            <span className="text-slate-400">New Total Monthly Surplus:</span>
            <span className="font-bold text-white text-sm">
              {formatINR(monthlySurplus + extraSavings)} / month{' '}
              <span className="text-emerald-400 text-xs font-normal">
                (+{formatINR(extraSavings)})
              </span>
            </span>
          </div>

          {/* Error Message if API fails */}
          {error && (
            <div className="rounded-xl bg-rose-950/30 p-3 border border-rose-500/30 text-xs text-rose-300">
              {error}
            </div>
          )}

          {/* Run Action Button */}
          <button
            type="button"
            disabled={isLoading || !selectedPlan}
            onClick={handleRunScenario}
            className="w-full py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-bold text-white shadow-lg shadow-cyan-600/25 transition flex items-center justify-center gap-2 cursor-pointer"
          >
            {isLoading ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Simulating Scenario (+{formatINR(extraSavings)}/mo)...</span>
              </>
            ) : (
              <span>Run What-If Analysis &rarr;</span>
            )}
          </button>
        </div>
      ) : (
        /* 4. Scenario Result Visualization (Before vs After) */
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-6 shadow-xl backdrop-blur-md flex flex-col gap-6 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                Simulation Results
              </span>
              <h3 className="text-lg font-bold text-white mt-0.5">
                Scenario Impact: +{formatINR(extraSavings)} / month extra savings
              </h3>
            </div>

            <button
              type="button"
              onClick={handleAdjustScenario}
              className="rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 px-3.5 py-2 text-xs font-semibold text-slate-200 transition cursor-pointer"
            >
              &larr; Adjust scenario
            </button>
          </div>

          {/* Before vs After Side-by-Side Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Column 1: Current Baseline */}
            <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Current Baseline
                </span>
                <span className="text-[11px] text-slate-400">₹45k Surplus</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800/40">
                  <span className="text-slate-400">Total Monthly Surplus:</span>
                  <span className="font-semibold text-white">{formatINR(monthlySurplus)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/40">
                  <span className="text-slate-400">Plan Commitment:</span>
                  <span className="font-semibold text-white">{formatINR(selectedPlan.monthly_investment)} / mo</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/40">
                  <span className="text-slate-400">Surplus Buffer Remaining:</span>
                  <span className={`font-bold ${baselineSurplusAfter >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {baselineSurplusAfter >= 0 ? `+${formatINR(baselineSurplusAfter)} / mo` : `${formatINR(baselineSurplusAfter)} / mo`}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/40">
                  <span className="text-slate-400">Success Probability:</span>
                  <span className="font-semibold text-white">{Math.round(selectedPlan.success_probability * 100)}%</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Affordability State:</span>
                  <span className={`font-semibold ${selectedPlan.feasible ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {selectedPlan.feasible ? '✓ Affordable' : '✕ Not Affordable'}
                  </span>
                </div>
              </div>
            </div>

            {/* Column 2: What-If Scenario */}
            <div className="rounded-xl bg-cyan-950/15 p-4 border border-cyan-500/30 space-y-3">
              <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                  What-If Scenario (+{formatINR(extraSavings)}/mo)
                </span>
                <span className="text-[11px] font-semibold text-cyan-300">Simulated Outcome</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-cyan-500/15">
                  <span className="text-slate-400">Total Monthly Surplus:</span>
                  <span className="font-bold text-cyan-300">{formatINR(scenarioSurplus)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-cyan-500/15">
                  <span className="text-slate-400">Plan Commitment:</span>
                  <span className="font-semibold text-white">{formatINR(scenarioPlan.monthly_investment)} / mo</span>
                </div>
                <div className="flex justify-between py-1 border-b border-cyan-500/15">
                  <span className="text-slate-400">Surplus Buffer Remaining:</span>
                  <span className={`font-bold ${scenarioSurplusAfter >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {scenarioSurplusAfter >= 0 ? `+${formatINR(scenarioSurplusAfter)} / mo` : `${formatINR(scenarioSurplusAfter)} / mo`}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-cyan-500/15">
                  <span className="text-slate-400">Success Probability:</span>
                  <span className="font-semibold text-white">{Math.round(scenarioPlan.success_probability * 100)}%</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Affordability State:</span>
                  <span className={`font-semibold ${scenarioPlan.feasible ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {scenarioPlan.feasible ? '✓ Affordable' : '✕ Not Affordable'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 5. What Changed Impact Explanation */}
          <div className="rounded-xl bg-slate-950/70 p-4 border border-slate-800 space-y-2 text-xs leading-relaxed">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-300">
              What Changed?
            </p>
            <p className="text-slate-300">
              Adding <strong className="text-white">+{formatINR(extraSavings)}/month</strong> raises your available monthly surplus from{' '}
              <strong className="text-white">{formatINR(monthlySurplus)}</strong> to{' '}
              <strong className="text-cyan-300">{formatINR(scenarioSurplus)}</strong>.
            </p>
            {!selectedPlan.feasible && scenarioPlan.feasible ? (
              <p className="text-emerald-400 font-medium">
                ✓ Strategy Shift: Plan {selectedPlan.plan_id} ({selectedPlan.label}) changes from <span className="text-rose-400 font-semibold">Not Affordable</span> to <span className="text-emerald-400 font-semibold">Fully Affordable</span> with a {formatINR(scenarioSurplusAfter)} monthly cushion!
              </p>
            ) : (
              <p className="text-slate-300">
                Your monthly cushion after funding Plan {selectedPlan.plan_id} expands from{' '}
                <strong className="text-white">{formatINR(baselineSurplusAfter)}</strong> to{' '}
                <strong className="text-emerald-400">{formatINR(scenarioSurplusAfter)}</strong>, providing higher tolerance against unexpected lifestyle shocks.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
