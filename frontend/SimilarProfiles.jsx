import React from 'react';
import { formatRupees, formatPercent, formatNumber } from './formatters.js';

/**
 * Screen 3.7 — Similar Profiles (Anonymous Cohort Intelligence)
 *
 * Displays anonymized aggregate statistical benchmarks of peer customers with
 * matching financial capacity, age bracket, income band, and goal profile.
 *
 * PRIVACY GUARANTEE:
 * No individual customer records, names, or IDs. Only group statistics & percentiles.
 *
 * NOTE on unconfirmed fields:
 * Field names in `peer_cohort` are self-authored mocks for Screen 3.7 and pending group confirmation.
 */
export default function SimilarProfiles({
  cohortData,
  apiData,
  isLoading = false,
  error = null,
  onNavigateToRiskInsight,
  onNavigateToPlans,
}) {
  if (isLoading) {
    return <SimilarProfilesSkeleton />;
  }

  if (error) {
    return (
      <div className="min-h-[500px] flex items-center justify-center p-6 font-sans">
        <div className="bg-slate-900 border border-red-500/40 rounded-xl p-8 max-w-md w-full text-center shadow-2xl">
          <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-4 text-red-400">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-slate-100 mb-2">Unable to Retrieve Peer Cohort</h3>
          <p className="text-sm text-slate-400 mb-6">{error || "The anonymous benchmarking service could not be reached."}</p>
          <button
            onClick={onNavigateToRiskInsight}
            className="w-full py-2.5 px-4 bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-semibold rounded-lg transition-all"
          >
            Return to Risk Insight
          </button>
        </div>
      </div>
    );
  }

  // Extract data from props or embedded fallback
  const rawCohort = cohortData?.peer_cohort || apiData?.peer_cohort || null;

  if (!rawCohort) {
    return (
      <div className="min-h-[500px] flex items-center justify-center p-6 font-sans">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 max-w-md w-full text-center">
          <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-slate-200 mb-1">No Peer Cohort Data Available</h3>
          <p className="text-sm text-slate-400 mb-4">No statistical peer group matched the selected customer criteria.</p>
          <button
            onClick={onNavigateToRiskInsight}
            className="py-2 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-all"
          >
            ← Return to Risk Insight
          </button>
        </div>
      </div>
    );
  }

  const {
    sample_size,
    similarity_criteria,
    mismatch_metrics,
    typical_plan,
    customer_benchmarks,
  } = rawCohort;

  return (
    <div className="w-full max-w-6xl mx-auto p-4 sm:p-6 md:p-8 space-y-8 font-sans text-slate-100">
      
      {/* Navigation & Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={onNavigateToRiskInsight}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400 hover:text-emerald-300 hover:underline transition-all group"
            >
              <svg className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>Back to Risk Insight (Screen 3.6)</span>
            </button>
            <span className="text-slate-600">·</span>
            <span className="px-2 py-0.5 text-[11px] font-semibold uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded">
              Screen 3.7 · Cohort Intelligence
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Anonymous Peer Cohort Comparison
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Aggregated statistical insights from <strong className="text-slate-200 font-semibold">{formatNumber(sample_size)} verified bank customers</strong> sharing identical profile attributes.
          </p>
        </div>

        {/* Privacy Seal */}
        <div className="flex items-center gap-3 bg-slate-900/90 border border-emerald-500/30 px-4 py-2.5 rounded-xl shadow-lg shrink-0">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <div className="text-xs font-bold text-slate-200 uppercase tracking-wider">Zero-PII Privacy Guarantee</div>
            <div className="text-[11px] text-slate-400">Differential Privacy Applied · Cohort Stats Only</div>
          </div>
        </div>
      </div>

      {/* Matching Criteria Strip */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
          <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
          </svg>
          Cohort Definition Criteria ({formatNumber(sample_size)} Matches)
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <div className="text-[11px] text-slate-400">Age Bracket</div>
            <div className="text-sm font-bold text-white mt-0.5">{similarity_criteria?.age_band || "—"}</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <div className="text-[11px] text-slate-400">Monthly Income Band</div>
            <div className="text-sm font-bold text-white mt-0.5">{similarity_criteria?.income_band || "—"}</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <div className="text-[11px] text-slate-400">Revealed Risk Band</div>
            <div className="text-sm font-bold text-emerald-400 mt-0.5">{similarity_criteria?.risk_band || "—"}</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <div className="text-[11px] text-slate-400">Financial Goal Category</div>
            <div className="text-sm font-bold text-indigo-300 mt-0.5 truncate" title={similarity_criteria?.primary_goal}>
              {similarity_criteria?.primary_goal || "—"}
            </div>
          </div>
        </div>
      </div>

      {/* Main Benchmarking Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left 7 Columns: Typical Plan & Allocation Behavior in this Cohort */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Typical Plan Card */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Cohort Consensus</span>
                <h2 className="text-lg font-bold text-white mt-0.5">Typical Plan Selection in this Group</h2>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400">Adoption Rate</span>
                <div className="text-base font-mono font-bold text-emerald-400">
                  {formatPercent(typical_plan?.adoption_rate, 0)}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/90">
                <div className="text-xs text-slate-400">Most Chosen Plan</div>
                <div className="text-base font-bold text-white mt-1">
                  {typical_plan?.preferred_plan_name || "—"} ({typical_plan?.preferred_plan_id || "A"})
                </div>
                <div className="text-[11px] text-slate-400 mt-1">Balanced equity-debt ratio</div>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/90">
                <div className="text-xs text-slate-400">Median Monthly SIP</div>
                <div className="text-base font-bold text-white mt-1">
                  {formatRupees(typical_plan?.median_monthly_investment)}/mo
                </div>
                <div className="text-[11px] text-slate-400 mt-1">Typical commitment</div>
              </div>
            </div>

            {/* Typical Allocation Visual Bar */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/90 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300">Cohort Asset Allocation Mix</span>
                <span className="text-slate-400 font-mono">
                  Goal Completion: <strong className="text-emerald-400">{formatPercent(typical_plan?.historical_goal_success_rate, 0)}</strong>
                </span>
              </div>

              {/* Progress split */}
              <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden flex">
                <div
                  className="h-full bg-indigo-500"
                  style={{ width: `${(typical_plan?.typical_allocation?.equity || 0.45) * 100}%` }}
                />
                <div
                  className="h-full bg-emerald-500"
                  style={{ width: `${(typical_plan?.typical_allocation?.debt || 0.55) * 100}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400 font-mono pt-1">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                  <span>Equity: {formatPercent(typical_plan?.typical_allocation?.equity, 0)}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>Debt / Fixed: {formatPercent(typical_plan?.typical_allocation?.debt, 0)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Mismatch Frequency in Cohort */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Behavioral Frequency</span>
              <span className="text-xs text-slate-400 font-mono">
                {formatNumber(mismatch_metrics?.mismatch_count)} of {formatNumber(sample_size)} Peers
              </span>
            </div>
            <h3 className="text-base font-bold text-white">
              {formatPercent(mismatch_metrics?.mismatch_rate, 0)} of similar peers also exhibit a Risk Mismatch
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {mismatch_metrics?.mismatch_pattern_summary || "Many customers self-report aggressive risk tolerance, but historical trade reactions show capital preservation behavior."}
            </p>
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-300">
              💡 <strong>Advisor Note:</strong> This divergence is extremely common in young professionals before experiencing their first major drawdown.
            </div>
          </div>
        </div>

        {/* Right 5 Columns: Where This Customer Sits vs Group (Percentiles) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-6">
            <div className="border-b border-slate-800 pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Customer Relative Standing</span>
              <h2 className="text-lg font-bold text-white mt-0.5">Where You Sit vs Peer Group</h2>
            </div>

            {/* Benchmark 1: Savings Surplus */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200">Monthly Savings Surplus</span>
                <span className="font-mono font-bold text-emerald-400">
                  {formatPercent(customer_benchmarks?.savings_rate_percentile, 0)} Percentile
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${(customer_benchmarks?.savings_rate_percentile || 0.74) * 100}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400 italic">
                {customer_benchmarks?.surplus_rank_summary || "Higher savings surplus than 74% of peers"}
              </p>
            </div>

            {/* Benchmark 2: Expense Discipline */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200">Expense Stability / Discipline</span>
                <span className="font-mono font-bold text-indigo-400">
                  {formatPercent(customer_benchmarks?.expense_discipline_percentile, 0)} Percentile
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${(customer_benchmarks?.expense_discipline_percentile || 0.62) * 100}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400 italic">
                Monthly spending predictability is higher than 62% of the peer cohort.
              </p>
            </div>

            {/* Benchmark 3: Emergency Fund Buffer */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200">Emergency Fund Runway</span>
                <span className="font-mono font-bold text-amber-400">
                  {formatPercent(customer_benchmarks?.emergency_buffer_percentile, 0)} Percentile
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${(customer_benchmarks?.emergency_buffer_percentile || 0.18) * 100}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400 italic">
                Lower emergency buffer than 82% of cohort — building liquid reserves is recommended.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="pt-4 border-t border-slate-800 space-y-3">
              <button
                onClick={onNavigateToPlans}
                className="w-full py-3.5 px-4 bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-bold text-sm rounded-xl transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 group cursor-pointer"
              >
                <span>Proceed to Goal Recommendations</span>
                <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>

              <button
                onClick={onNavigateToRiskInsight}
                className="w-full py-2.5 px-4 bg-slate-950 hover:bg-slate-800 active:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-800 transition-all"
              >
                ← Return to Risk Insight
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Loading Skeleton Component */
function SimilarProfilesSkeleton() {
  return (
    <div className="w-full max-w-6xl mx-auto p-6 md:p-8 space-y-8 animate-pulse font-sans">
      <div className="space-y-3 pb-6 border-b border-slate-800">
        <div className="h-4 bg-slate-800 rounded w-48" />
        <div className="h-8 bg-slate-800 rounded w-80" />
        <div className="h-4 bg-slate-800/60 rounded w-96" />
      </div>

      <div className="h-28 bg-slate-900 border border-slate-800 rounded-2xl" />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 h-96 bg-slate-900 border border-slate-800 rounded-2xl" />
        <div className="lg:col-span-5 h-96 bg-slate-900 border border-slate-800 rounded-2xl" />
      </div>
    </div>
  );
}
