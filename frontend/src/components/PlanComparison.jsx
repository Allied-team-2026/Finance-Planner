import { useState } from 'react'
import PlanCard from './PlanCard'
import PlanDetailsModal from './PlanDetailsModal'

export default function PlanComparison({
  plans = [],
  goalPriorityNote,
  nSimulations,
  selectedPlanId: propSelectedPlanId,
  onSelectPlan,
}) {
  // Local state fallback if not passed from parent
  const [internalSelectedPlanId, setInternalSelectedPlanId] = useState('A')

  // State to track which plan is being inspected in the modal
  const [inspectingPlan, setInspectingPlan] = useState(null)

  const selectedPlanId = propSelectedPlanId !== undefined ? propSelectedPlanId : internalSelectedPlanId
  const handleSelectPlan = (planId) => {
    if (onSelectPlan) {
      onSelectPlan(planId)
    } else {
      setInternalSelectedPlanId(planId)
    }
  }

  if (!plans || plans.length === 0) return null

  const activePlan = plans.find((p) => p.plan_id === selectedPlanId) || plans[0]

  return (
    <section id="plans-section" className="flex flex-col gap-6 scroll-mt-8">
      {/* Comparison Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-indigo-500/10 px-2.5 py-1 text-[11px] font-semibold text-indigo-400 border border-indigo-500/20">
              Decision Intelligence Engine
            </span>
            <span className="text-xs text-slate-400">
              {nSimulations == null
                ? 'Validated against simulation'
                : `Validated against ${nSimulations.toLocaleString('en-IN')} simulations`}
            </span>
          </div>

          <h2 className="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Compare your personalized strategies
          </h2>

          <p className="mt-1.5 max-w-3xl text-sm text-slate-400 leading-relaxed">
            Each plan balances growth, affordability, risk, and stress resilience differently.
          </p>
        </div>

        {/* AI & Methodology Badges */}
        <div className="flex flex-wrap gap-2 text-xs">
          <div className="flex items-center gap-1.5 rounded-lg bg-[#0e1626] px-3 py-1.5 border border-slate-800 text-slate-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <span>Stress-tested for adverse shocks</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-lg bg-[#0e1626] px-3 py-1.5 border border-slate-800 text-slate-300">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
            <span>NIFTY 2005–2025 Market Grounded</span>
          </div>
        </div>
      </div>

      {/* 3 Stable Plan Cards Grid (No vertical resizing or layout shifting) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {plans.map((plan) => (
          <PlanCard
            key={plan.plan_id}
            plan={plan}
            isSelected={selectedPlanId === plan.plan_id}
            onSelect={() => handleSelectPlan(plan.plan_id)}
            onViewDetails={(p) => setInspectingPlan(p)}
            nSimulations={nSimulations}
          />
        ))}
      </div>

      {/* Action Bar: Challenge, What-If, and Selected Summary Navigation */}
      <div className="rounded-2xl bg-gradient-to-r from-[#0d1322] via-[#111a2e] to-[#0d1322] p-4 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <div>
            <p className="text-xs text-slate-300">
              Selected Strategy:{' '}
              <strong className="text-white">
                Plan {activePlan?.plan_id} ({activePlan?.label})
              </strong>
            </p>
            <p className="text-[11px] text-slate-400">
              Explore scenarios, test with Challenger AI, or review final strategy summary.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          <a
            href="#whatif-section"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 rounded-xl bg-cyan-600/90 hover:bg-cyan-500 px-3.5 py-2 text-xs font-semibold text-white shadow-md shadow-cyan-600/20 transition cursor-pointer"
          >
            <span>What-If Analysis</span>
            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </a>

          <a
            href="#challenge-section"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-3.5 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/25 transition cursor-pointer"
          >
            <span>Challenge Pick</span>
            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </a>

          <a
            href="#summary-section"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 rounded-xl bg-emerald-600/90 hover:bg-emerald-500 px-3.5 py-2 text-xs font-semibold text-white shadow-md shadow-emerald-600/25 transition cursor-pointer"
          >
            <span>Review Summary</span>
            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </a>
        </div>
      </div>

      {/* Goal Priority & Horizon Note from JSON */}
      {goalPriorityNote && (
        <div className="rounded-xl bg-[#090f1e]/90 p-4 border border-slate-800/80 flex items-start gap-3 text-xs text-slate-300">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
          </div>
          <div>
            <span className="font-semibold text-white">Goal Prioritization Rationale: </span>
            <span className="text-slate-300">{goalPriorityNote}</span>
          </div>
        </div>
      )}

      {/* Dedicated Plan Details Modal (Opening does not auto-select the plan) */}
      {inspectingPlan && (
        <PlanDetailsModal
          plan={inspectingPlan}
          isSelected={selectedPlanId === inspectingPlan.plan_id}
          onClose={() => setInspectingPlan(null)}
          onSelect={() => {
            handleSelectPlan(inspectingPlan.plan_id)
            setInspectingPlan(null)
          }}
          onChallenge={() => {
            handleSelectPlan(inspectingPlan.plan_id)
            setInspectingPlan(null)
            const el = document.getElementById('challenge-section')
            if (el) el.scrollIntoView({ behavior: 'smooth' })
          }}
          onWhatIf={() => {
            handleSelectPlan(inspectingPlan.plan_id)
            setInspectingPlan(null)
            const el = document.getElementById('whatif-section')
            if (el) el.scrollIntoView({ behavior: 'smooth' })
          }}
        />
      )}
    </section>
  )
}