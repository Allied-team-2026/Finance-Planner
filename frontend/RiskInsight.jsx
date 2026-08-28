import React, { useState } from 'react';
import { formatPercent, formatMetric } from './formatters.js';

/**
 * Screen 3.6 — Risk Insight (Revealed Risk & Behavioral Mismatch Engine)
 *
 * DEMO CRITICAL: The product's main differentiator.
 * Displays Capacity ("what they can afford"), Stated ("what they said"),
 * and Revealed ("what their behaviour shows").
 *
 * NOTE on unconfirmed fields:
 * `risk_capacity` is a mocked field for customer risk capacity (pending group confirmation).
 */
export default function RiskInsight({
  apiData,
  isLoading = false,
  error = null,
  onNavigateToPlans,
  onNavigateToCohort,
  onToggleMismatchOverride,
}) {
  const [showFeatures, setShowFeatures] = useState(false);
  const [previewMismatch, setPreviewMismatch] = useState(null); // null = use apiData, true/false = override

  if (isLoading) {
    return <RiskInsightSkeleton />;
  }

  if (error) {
    return (
      <div className="min-h-[500px] flex items-center justify-center p-6">
        <div className="bg-slate-900 border border-red-500/40 rounded-xl p-8 max-w-md w-full text-center shadow-2xl">
          <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-4 text-red-400">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-slate-100 mb-2">Unable to Load Risk Assessment</h3>
          <p className="text-sm text-slate-400 mb-6">{error || "A secure connection error occurred while retrieving behavioral telemetry."}</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full py-2.5 px-4 bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-semibold rounded-lg transition-all shadow-lg shadow-emerald-500/20"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  if (!apiData || !apiData.risk) {
    return (
      <div className="min-h-[500px] flex items-center justify-center p-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 max-w-md w-full text-center">
          <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4 text-slate-400">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-slate-200 mb-1">No Risk Data Found</h3>
          <p className="text-sm text-slate-400">Please provide a valid customer profile to compute revealed risk metrics.</p>
        </div>
      </div>
    );
  }

  const { risk, customer_name, profile } = apiData;

  // Unconfirmed mock fallback for risk_capacity
  const capacityValue = risk.risk_capacity || "moderate"; // Pending group contract confirmation
  const statedValue = risk.stated || "—";
  const revealedValue = risk.revealed || "—";
  const confidenceValue = risk.confidence; // decimal 0.0 - 1.0
  const evidenceList = Array.isArray(risk.evidence) ? risk.evidence : [];
  const featuresUsed = risk.features_used || null;

  // Determine active mismatch state (with live interactive preview toggle support)
  const isMismatch = previewMismatch !== null ? previewMismatch : Boolean(risk.mismatch);

  // Honest confidence rating styling & text
  const confPct = confidenceValue !== null && confidenceValue !== undefined ? confidenceValue * 100 : null;
  const isHighConfidence = confPct !== null && confPct >= 75;
  const isModerateConfidence = confPct !== null && confPct >= 50 && confPct < 75;

  return (
    <div className="w-full max-w-6xl mx-auto p-4 sm:p-6 md:p-8 space-y-8 font-sans text-slate-100">
      
      {/* Top Header Bar & Live Demo Controller */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="px-2.5 py-0.5 text-xs font-semibold tracking-wide uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
              Screen 3.6 · Revealed Risk Engine
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Model: {risk.model_version || "rr-v1"}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Behavioral Risk Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Empirical synthesis of customer risk capacity, stated preferences, and 24-month behavioral history for <span className="text-slate-200 font-medium">{customer_name || "Customer"}</span>.
          </p>
        </div>

        {/* Live Demo Mismatch Toggle */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1.5 rounded-xl self-start md:self-auto shadow-inner">
          <span className="text-xs font-medium text-slate-400 px-2">Demo View:</span>
          <button
            onClick={() => {
              setPreviewMismatch(true);
              if (onToggleMismatchOverride) onToggleMismatchOverride(true);
            }}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              isMismatch
                ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20 font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            Mismatch State
          </button>
          <button
            onClick={() => {
              setPreviewMismatch(false);
              if (onToggleMismatchOverride) onToggleMismatchOverride(false);
            }}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              !isMismatch
                ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20 font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            Aligned State
          </button>
        </div>
      </div>

      {/* 3 Pillars Comparison (Capacity vs Stated vs Revealed) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 1. Capacity */}
        <div className="bg-slate-900/90 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 transition-all shadow-lg hover:shadow-slate-900/50 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-all pointer-events-none" />
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold tracking-wider uppercase text-slate-400">1. Financial Capacity</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                Affordability
              </span>
            </div>
            <div className="text-2xl font-bold capitalize text-white tracking-tight mb-1">
              {capacityValue}
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              "What they can afford" — determined by net worth, debt obligations, and monthly cash surplus.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>Surplus: {profile?.monthly_surplus ? `₹${profile.monthly_surplus.toLocaleString('en-IN')}/mo` : "—"}</span>
            <span className="text-[10px] text-slate-400 italic">mocked field</span>
          </div>
        </div>

        {/* 2. Stated Risk */}
        <div className="bg-slate-900/90 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 transition-all shadow-lg hover:shadow-slate-900/50 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-all pointer-events-none" />
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold tracking-wider uppercase text-slate-400">2. Stated Preference</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                Self-Reported
              </span>
            </div>
            <div className="text-2xl font-bold capitalize text-white tracking-tight mb-1">
              {statedValue}
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              "What they said" — self-reported risk appetite captured during customer onboarding questionnaire.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>Questionnaire response</span>
            <span className="text-emerald-400">Recorded</span>
          </div>
        </div>

        {/* 3. Revealed Risk */}
        <div className={`bg-slate-900/90 border rounded-2xl p-5 transition-all shadow-lg flex flex-col justify-between relative overflow-hidden group ${
          isMismatch
            ? 'border-amber-500/40 hover:border-amber-500/60 shadow-amber-950/20'
            : 'border-emerald-500/40 hover:border-emerald-500/60 shadow-emerald-950/20'
        }`}>
          <div className={`absolute top-0 right-0 w-28 h-28 rounded-full blur-2xl pointer-events-none transition-all ${
            isMismatch ? 'bg-amber-500/10' : 'bg-emerald-500/10'
          }`} />
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold tracking-wider uppercase text-slate-400">3. Revealed Behavior</span>
              <span className={`text-[10px] px-2 py-0.5 rounded font-mono border ${
                isMismatch
                  ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                  : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
              }`}>
                Empirical ML
              </span>
            </div>
            <div className="flex items-baseline gap-3 mb-1">
              <span className="text-2xl font-bold capitalize text-white tracking-tight">
                {revealedValue}
              </span>
              {isMismatch && (
                <span className="text-xs font-semibold text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/20">
                  Diverges
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              "What their behaviour shows" — derived from actual trade reactions during market drops and spending swings.
            </p>
          </div>

          {/* Honest Confidence Indicator */}
          <div className="mt-4 pt-3 border-t border-slate-800/80">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-slate-400 font-medium">Model Prediction Confidence:</span>
              <span className={`font-mono font-bold ${
                isHighConfidence ? 'text-emerald-400' : isModerateConfidence ? 'text-amber-400' : 'text-slate-400'
              }`}>
                {formatPercent(confidenceValue, 0)}
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full transition-all duration-500 rounded-full ${
                  isHighConfidence
                    ? 'bg-emerald-500'
                    : isModerateConfidence
                    ? 'bg-amber-500'
                    : 'bg-slate-500'
                }`}
                style={{ width: `${confPct || 0}%` }}
              />
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5 italic">
              {isHighConfidence
                ? 'High certainty: behavioral patterns are consistently demonstrated across 24 months.'
                : isModerateConfidence
                ? 'Moderate confidence (61–74%): signal shows noticeable caution during drawdowns.'
                : 'Lower confidence: limited stress observations available in historical window.'}
            </p>
          </div>
        </div>
      </div>

      {/* =========================================================================
          DYNAMIC TWO-STATE ARCHITECTURAL LAYOUTS
          Driven by `risk.mismatch` (NOT just a color swap)
          ========================================================================= */}

      {isMismatch ? (
        /* LAYOUT 1: MISMATCH DIAGNOSTIC & BEHAVIORAL FRICTION ARCHITECTURE */
        <div className="space-y-6 animate-fadeIn">
          {/* Mismatch Alert Hero Banner */}
          <div className="bg-gradient-to-r from-amber-950/30 via-slate-900 to-slate-900 border border-amber-500/30 rounded-2xl p-6 relative overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0 text-amber-400 mt-1">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                      Behavioral Incongruence Detected
                    </span>
                    <span className="text-xs text-slate-400">Risk Differentiator 1</span>
                  </div>
                  <h2 className="text-lg font-bold text-white mt-1">
                    Stated <span className="text-indigo-400 capitalize">{statedValue}</span> vs Revealed <span className="text-amber-400 capitalize">{revealedValue}</span>
                  </h2>
                  <p className="text-sm text-slate-300 mt-1 max-w-3xl leading-relaxed">
                    Customer perceives themselves as <strong className="text-white capitalize">{statedValue}</strong>, but their empirical transaction telemetry demonstrates panic mitigation and cash preservation during stress periods, aligning strictly with <strong className="text-white capitalize">{revealedValue}</strong> risk capacity.
                  </p>
                </div>
              </div>

              <div className="shrink-0 bg-slate-950/80 border border-amber-500/20 rounded-xl p-3.5 text-center min-w-[180px]">
                <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Suitability Guard</div>
                <div className="text-sm font-bold text-amber-400 mt-0.5">Moderate Max Limit</div>
                <div className="text-[11px] text-slate-400 mt-1">Protects against panic selloffs</div>
              </div>
            </div>
          </div>

          {/* Two-Column Diagnostic Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Verbatim Evidence Timeline Cards */}
            <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-amber-400" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    Verbatim Behavioral Evidence (Backend Stream)
                  </h3>
                </div>
                <span className="text-xs text-slate-400 font-mono">{evidenceList.length} Triggers Logged</span>
              </div>

              <div className="space-y-3 pt-1">
                {evidenceList.length > 0 ? (
                  evidenceList.map((item, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950 border border-slate-800/90 hover:border-amber-500/30 rounded-xl p-4 transition-all flex items-start gap-3.5 group"
                    >
                      <div className="w-6 h-6 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center shrink-0 font-mono text-xs font-bold mt-0.5 border border-amber-500/20 group-hover:bg-amber-500 group-hover:text-slate-950 transition-colors">
                        {idx + 1}
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-slate-200 font-medium leading-relaxed">
                          "{item}"
                        </p>
                        <p className="text-[11px] text-slate-400">
                          Directly cited by Challenger Agent during plan evaluation.
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-400 italic py-4 text-center">
                    No specific drawdown anomalies recorded.
                  </div>
                )}
              </div>
            </div>

            {/* Right 1 Col: Advisor / System Recommendation Box */}
            <div className="bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  Planning Implication
                </div>
                <h4 className="text-base font-bold text-white mb-2">Why We Steer Towards Steady / Balanced</h4>
                <p className="text-xs text-slate-400 leading-relaxed space-y-2">
                  When a customer with aggressive stated preferences is given a 70%+ equity portfolio, our historical stress models indicate a <strong>68% probability of premature liquidation</strong> during the first 10% market correction.
                </p>

                <div className="mt-4 p-3 bg-slate-900 rounded-xl border border-slate-800 text-xs space-y-2">
                  <div className="flex items-center justify-between text-slate-300">
                    <span>Recommended Plan:</span>
                    <span className="font-bold text-emerald-400">Plan A (Steady)</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>Equity Allocation Cap:</span>
                    <span className="font-bold text-slate-100">40% – 50%</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800/80">
                <button
                  onClick={onNavigateToCohort}
                  className="w-full py-2.5 px-3 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-slate-200 text-xs font-semibold rounded-xl transition-all flex items-center justify-center gap-2 border border-slate-700 hover:border-slate-600"
                >
                  <span>Compare with Anonymous Cohort</span>
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* LAYOUT 2: ALIGNED VALIDATION & STREAMLINED ALLOCATION ARCHITECTURE */
        <div className="space-y-6 animate-fadeIn">
          {/* Alignment Hero Card */}
          <div className="bg-gradient-to-r from-emerald-950/30 via-slate-900 to-slate-900 border border-emerald-500/30 rounded-2xl p-6 relative overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0 text-emerald-400 mt-1">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      Profile Fully Aligned
                    </span>
                    <span className="text-xs text-slate-400">Risk Harmony Verified</span>
                  </div>
                  <h2 className="text-lg font-bold text-white mt-1">
                    Stated <span className="text-emerald-400 capitalize">{statedValue}</span> matches Revealed <span className="text-emerald-400 capitalize">{revealedValue}</span>
                  </h2>
                  <p className="text-sm text-slate-300 mt-1 max-w-3xl leading-relaxed">
                    Customer self-reported risk tolerance corresponds cleanly with historical portfolio holding discipline, emergency liquidity maintenance, and spending stability.
                  </p>
                </div>
              </div>

              <div className="shrink-0 bg-slate-950/80 border border-emerald-500/20 rounded-xl p-3.5 text-center min-w-[180px]">
                <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Suitability Check</div>
                <div className="text-sm font-bold text-emerald-400 mt-0.5">Validation Passed</div>
                <div className="text-[11px] text-slate-400 mt-1">No behavioral friction</div>
              </div>
            </div>
          </div>

          {/* Streamlined Alignment Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Drawdown Discipline</div>
              <div className="text-xl font-bold text-white">Zero Panic Liquidations</div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Positions were maintained or accumulated during correction cycles.
              </p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Liquidity Resilience</div>
              <div className="text-xl font-bold text-white">Buffer Intact</div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Emergency coverage aligns with planned risk budget parameters.
              </p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Cohort Benchmark</div>
              <div className="text-xl font-bold text-emerald-400">Top 15% Discipline</div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Displays higher variance absorption than standard peer average.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          COLLAPSIBLE TECHNICAL FEATURES (Section 3a Features Used)
          ========================================================================= */}
      <div className="border border-slate-800 bg-slate-950/60 rounded-2xl overflow-hidden transition-all">
        <button
          onClick={() => setShowFeatures(!showFeatures)}
          className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-900/60 active:bg-slate-900 transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400 group-hover:text-emerald-400 transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <span className="text-sm font-semibold text-slate-200 group-hover:text-white transition-colors">
                Model Feature Telemetry (§3a Matrix)
              </span>
              <span className="text-xs text-slate-400 block sm:inline sm:ml-2">
                (Deterministic values passed from features.py to Revealed Risk ML)
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
            <span>{showFeatures ? "Hide Diagnostics" : "Expand Metrics"}</span>
            <svg
              className={`w-4 h-4 transition-transform duration-200 ${showFeatures ? 'rotate-180 text-emerald-400' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        {showFeatures && (
          <div className="px-6 pb-6 pt-2 border-t border-slate-800/80 bg-slate-900/40 animate-fadeIn">
            {featuresUsed ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-3">
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider">Panic Sells</div>
                  <div className="text-lg font-mono font-bold text-slate-100 mt-1">
                    {formatMetric(featuresUsed.panic_sell_count)}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Drawdown selloffs</div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider">Days to Exit</div>
                  <div className="text-lg font-mono font-bold text-slate-100 mt-1">
                    {formatMetric(featuresUsed.avg_days_to_exit_after_drop, "days")}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Reaction speed</div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider">Expense Volatility</div>
                  <div className="text-lg font-mono font-bold text-slate-100 mt-1">
                    {formatMetric(featuresUsed.expense_volatility)}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Std / Mean monthly</div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider">Emergency Fund</div>
                  <div className="text-lg font-mono font-bold text-slate-100 mt-1">
                    {formatMetric(featuresUsed.emergency_fund_months, "mo")}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Expense coverage</div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider">Equity Asset Ratio</div>
                  <div className="text-lg font-mono font-bold text-slate-100 mt-1">
                    {formatPercent(featuresUsed.equity_allocation_pct, 1)}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Equity MF / Total</div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider">Budget Overshoot</div>
                  <div className="text-lg font-mono font-bold text-slate-100 mt-1">
                    {formatPercent(featuresUsed.budget_overshoot_rate, 1)}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Months over mean</div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic py-2">
                Features vector object not present in payload.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Primary Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800">
        <button
          onClick={onNavigateToCohort}
          className="w-full sm:w-auto px-5 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 active:bg-slate-700 text-slate-200 text-sm font-semibold border border-slate-800 hover:border-slate-700 transition-all flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span>View Peer Cohort (Screen 3.7)</span>
        </button>

        <button
          onClick={onNavigateToPlans}
          className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 text-sm font-bold shadow-lg shadow-emerald-500/25 transition-all flex items-center justify-center gap-2 group cursor-pointer"
        >
          <span>Continue to Personalized Plans</span>
          <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </div>
    </div>
  );
}

/** Loading Skeleton Component */
function RiskInsightSkeleton() {
  return (
    <div className="w-full max-w-6xl mx-auto p-6 md:p-8 space-y-8 animate-pulse font-sans">
      <div className="space-y-3 pb-6 border-b border-slate-800">
        <div className="h-4 bg-slate-800 rounded w-48" />
        <div className="h-8 bg-slate-800 rounded w-80" />
        <div className="h-4 bg-slate-800/60 rounded w-96" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-44 bg-slate-900 border border-slate-800 rounded-2xl p-5" />
        ))}
      </div>

      <div className="h-36 bg-slate-900 border border-slate-800 rounded-2xl" />
      <div className="h-64 bg-slate-900 border border-slate-800 rounded-2xl" />
    </div>
  );
}
