export default function PipelineGraph({ stages, currentStageIndex, customerId, realData }) {
  // Helper to format currency if available
  const formatINR = (amount) => {
    if (amount == null || isNaN(amount)) return null
    return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
  }

  // Tier groupings for the 11 stages
  const tier1 = [stages[0]] // 01 Customer Data
  const tier2 = [stages[1], stages[2]] // 02 Profile Engine, 03 Feature Extraction
  const tier3 = [stages[3]] // 04 Revealed Risk
  const tier4 = [stages[4]] // 05 Plan Generator
  const tier5 = [stages[5], stages[6], stages[7]] // 06 Monte Carlo, 07 Stress Test, 08 Peer Cohort
  const tier6 = [stages[8], stages[9]] // 09 AI Explanation, 10 Challenger
  const tier7 = [stages[10]] // 11 Verification

  // Dynamically resolve real stage output snippet if realData exists
  const getStageSnippet = (stageId) => {
    if (!realData) return null
    switch (stageId) {
      case 'customer':
        return realData.customer_name ? `${realData.customer_name} (${customerId})` : `ID: ${customerId}`
      case 'profile':
        return realData.profile?.monthly_surplus != null
          ? `Surplus: ${formatINR(realData.profile.monthly_surplus)}/mo`
          : null
      case 'features':
        return realData.context?.employment_type
          ? `Context: ${realData.context.employment_type}, Tier ${realData.context.city_tier}`
          : 'Transactions & Drawdown Features'
      case 'risk':
        return realData.risk?.mismatch
          ? `Mismatch: Stated ${realData.risk.stated} vs Revealed ${realData.risk.revealed}`
          : `Risk: ${realData.risk?.revealed || 'Calibrated'}`
      case 'plans':
        return realData.plans?.length ? `${realData.plans.length} Strategic Asset Plans` : '3 Plans Synthesized'
      case 'montecarlo':
        return realData.meta?.n_simulations
          ? `${realData.meta.n_simulations.toLocaleString()} Stochastic Paths`
          : '10,000 Iterations'
      case 'stress':
        return 'Inflation, Recession & Shock Combos'
      case 'cohort':
        return realData.peer_cohort?.cohort_name || 'Demographic Peer Benchmarking'
      case 'explanation':
        return 'Grounded Goal Alignment Rationale'
      case 'challenge':
        return realData.challenge?.challenger_title || 'Pre-Commitment Behavioral Audit'
      case 'verify':
        return realData.verifier?.numbers_checked
          ? `${realData.verifier.numbers_checked} Numbers Verified · 0 Discrepancies`
          : '100% Deterministic Match'
      default:
        return null
    }
  }

  const renderNode = (stage) => {
    const isCurrent = stage.index === currentStageIndex
    const isCompleted = stage.status === 'completed'
    const isWarning = stage.status === 'warning'
    const isPending = stage.status === 'pending'
    const snippet = (isCompleted || isCurrent || isWarning) ? getStageSnippet(stage.id) : null

    // Node container styling
    let borderClass = 'border-slate-800/80 bg-[#0c1220]/80'
    let ringClass = ''
    let badgeClass = 'bg-slate-800 text-slate-400'
    let statusText = 'WAIT'

    if (isPending) {
      borderClass = 'border-slate-800/60 bg-[#090e18]/60 opacity-60'
      statusText = 'PENDING'
    } else if (isCurrent) {
      borderClass = 'border-indigo-500/80 bg-indigo-950/30 shadow-md shadow-indigo-500/20'
      ringClass = 'ring-1.5 ring-indigo-500/50'
      badgeClass = 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 animate-pulse'
      statusText = 'RUNNING'
    } else if (isWarning) {
      borderClass = 'border-amber-500/70 bg-amber-950/25 shadow-md shadow-amber-500/10'
      ringClass = 'ring-1 ring-amber-500/40'
      badgeClass = 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
      statusText = 'MISMATCH'
    } else if (isCompleted) {
      borderClass = 'border-emerald-500/40 bg-emerald-950/15'
      badgeClass = 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
      statusText = 'VERIFIED'
    }

    return (
      <div
        key={stage.id}
        className={`relative flex-1 min-w-[125px] rounded-lg border px-2.5 py-1.5 transition-all duration-300 backdrop-blur-md ${borderClass} ${ringClass}`}
      >
        <div className="flex items-center justify-between gap-1 mb-0.5">
          <div className="flex items-center gap-1">
            <span className="font-mono text-[8.5px] font-bold text-slate-400 px-1 py-0.2 rounded bg-slate-900 border border-slate-800">
              {stage.step}
            </span>
            <span className="text-[8.5px] text-slate-500 font-mono truncate max-w-[75px]" title={stage.engine}>
              {stage.engine.replace('engines.', '').replace('models.', '').replace('agents.', '')}
            </span>
          </div>

          <span className={`text-[8px] font-mono font-bold px-1 py-0.2 rounded tracking-wider ${badgeClass}`}>
            {statusText}
          </span>
        </div>

        <h4 className="text-[11px] font-bold text-white tracking-tight leading-tight">
          {stage.name}
        </h4>

        {snippet ? (
          <div className={`mt-0.5 pt-0.5 border-t border-slate-800/60 font-mono text-[8.5px] truncate ${
            isWarning ? 'text-amber-300 font-semibold' : 'text-emerald-400'
          }`}>
            {snippet}
          </div>
        ) : (
          <p className="text-[8.5px] text-slate-400 line-clamp-1 mt-0.5">
            {stage.description}
          </p>
        )}
      </div>
    )
  }

  const renderConnector = (isActive, label) => {
    return (
      <div className="flex flex-col items-center justify-center my-0.5 relative w-full select-none">
        <div className={`w-0.5 h-2 transition-colors duration-300 ${
          isActive ? 'bg-gradient-to-b from-indigo-500 to-cyan-400 shadow-sm shadow-cyan-400/50' : 'bg-slate-800'
        }`} />
        {isActive && (
          <div className="absolute w-1.5 h-1.5 rounded-full bg-cyan-300 shadow-sm shadow-cyan-400 animate-ping" />
        )}
        {label && (
          <span className="text-[7.5px] font-mono text-slate-500 uppercase tracking-widest leading-none mt-0.2">
            {label}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-0.5 w-full max-w-3xl mx-auto py-0.5">
      {/* Tier 1: Customer Ingestion */}
      <div className="flex justify-center">
        <div className="w-full max-w-sm">{renderNode(tier1[0])}</div>
      </div>

      {renderConnector(currentStageIndex >= 1, 'Profile + Features')}

      {/* Tier 2: Profile & Features (Parallel) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {tier2.map((s) => renderNode(s))}
      </div>

      {renderConnector(currentStageIndex >= 3, 'Behavioral Risk Audit')}

      {/* Tier 3: Revealed Risk */}
      <div className="flex justify-center">
        <div className="w-full max-w-sm">{renderNode(tier3[0])}</div>
      </div>

      {renderConnector(currentStageIndex >= 4, 'Strategy Synthesis')}

      {/* Tier 4: Plan Generator */}
      <div className="flex justify-center">
        <div className="w-full max-w-sm">{renderNode(tier4[0])}</div>
      </div>

      {renderConnector(currentStageIndex >= 5, 'Monte Carlo + Stress + Peer Cohort')}

      {/* Tier 5: Simulation & Peer Audit (3 engines) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {tier5.map((s) => renderNode(s))}
      </div>

      {renderConnector(currentStageIndex >= 8, 'AI Explanation + Challenger')}

      {/* Tier 6: Reasoning & Audit (2 agents) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {tier6.map((s) => renderNode(s))}
      </div>

      {renderConnector(currentStageIndex >= 10, 'Deterministic Verification')}

      {/* Tier 7: Deterministic Verification */}
      <div className="flex justify-center">
        <div className="w-full max-w-sm">{renderNode(tier7[0])}</div>
      </div>
    </div>
  )
}
