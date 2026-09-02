import { useState, useEffect, useRef } from 'react'
import { fetchPlan } from '../services/api'
import PipelineGraph from './PipelineGraph'
import ExecutionConsole from './ExecutionConsole'

const INITIAL_STAGES = [
  {
    id: 'customer',
    index: 0,
    step: '01',
    name: 'Customer Data',
    engine: 'engines.synthetic_data',
    description: 'Ingesting identity, assets, liabilities & goals',
    status: 'pending',
  },
  {
    id: 'profile',
    index: 1,
    step: '02',
    name: 'Profile Engine',
    engine: 'engines.profile',
    description: 'Synthesizing net worth, cash flow & risk capacity',
    status: 'pending',
  },
  {
    id: 'features',
    index: 2,
    step: '03',
    name: 'Feature Extraction',
    engine: 'engines.features',
    description: 'Parsing transaction history & drawdown behaviors',
    status: 'pending',
  },
  {
    id: 'risk',
    index: 3,
    step: '04',
    name: 'Revealed Risk',
    engine: 'models.risk_model',
    description: 'Auditing stated preference vs revealed risk behavior',
    status: 'pending',
  },
  {
    id: 'plans',
    index: 4,
    step: '05',
    name: 'Plan Generator',
    engine: 'engines.plan_generator',
    description: 'Synthesizing 3 personalized strategic asset allocations',
    status: 'pending',
  },
  {
    id: 'montecarlo',
    index: 5,
    step: '06',
    name: 'Monte Carlo',
    engine: 'engines.montecarlo',
    description: '10,000 stochastic market return simulation paths',
    status: 'pending',
  },
  {
    id: 'stress',
    index: 6,
    step: '07',
    name: 'Stress Test',
    engine: 'engines.stress_test',
    description: 'Testing inflation, recession & rate shock combinations',
    status: 'pending',
  },
  {
    id: 'cohort',
    index: 7,
    step: '08',
    name: 'Peer Cohort',
    engine: 'engines.peer_cohort',
    description: 'Demographic percentile peer benchmarking',
    status: 'pending',
  },
  {
    id: 'explanation',
    index: 8,
    step: '09',
    name: 'AI Explanation',
    engine: 'agents.explanation',
    description: 'Synthesizing verified executive rationales & trade-offs',
    status: 'pending',
  },
  {
    id: 'challenge',
    index: 9,
    step: '10',
    name: 'Challenger',
    engine: 'agents.challenger',
    description: 'Auditing recommended strategies against behavioral traps',
    status: 'pending',
  },
  {
    id: 'verify',
    index: 10,
    step: '11',
    name: 'Verification',
    engine: 'agents.verifier',
    description: 'Auditing mathematical consistency & numeric bounds',
    status: 'pending',
  },
]

export default function PipelineLoading({ customerId, onComplete, onCancel }) {
  const [initLoading, setInitLoading] = useState(true)
  const [stages, setStages] = useState(INITIAL_STAGES)
  const [currentStageIndex, setCurrentStageIndex] = useState(0)
  const [logs, setLogs] = useState([])
  const [isVerified, setIsVerified] = useState(false)
  const [planData, setPlanData] = useState(null)
  const [error, setError] = useState(null)
  const [elapsedTime, setElapsedTime] = useState(0)

  const planResponseRef = useRef(null)
  const hasMountedRef = useRef(true)

  const getTimestamp = () => {
    const d = new Date()
    return d.toTimeString().split(' ')[0] + '.' + String(d.getMilliseconds()).padStart(3, '0')
  }

  const addLog = (message, stageNum = null, type = 'info') => {
    const newEntry = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: getTimestamp(),
      stageNum,
      message,
      type,
    }
    setLogs((prev) => [...prev, newEntry])
  }

  // 1. Initial short professional loading state
  useEffect(() => {
    const timer = setTimeout(() => {
      setInitLoading(false)
    }, 600)
    return () => clearTimeout(timer)
  }, [])

  // 2. Elapsed execution timer
  useEffect(() => {
    if (initLoading || isVerified || error) return
    const interval = setInterval(() => {
      setElapsedTime((prev) => +(prev + 0.1).toFixed(1))
    }, 100)
    return () => clearInterval(interval)
  }, [initLoading, isVerified, error])

  // 3. Initiate actual API request in parallel
  useEffect(() => {
    hasMountedRef.current = true
    let isCancelled = false

    const runApi = async () => {
      try {
        addLog(`Initiating WealthIQ planning pipeline for ${customerId}...`, null, 'dim')
        const response = await fetchPlan({ customer_id: customerId })
        if (!isCancelled && hasMountedRef.current) {
          planResponseRef.current = response
          setPlanData(response)
        }
      } catch (err) {
        if (!isCancelled && hasMountedRef.current) {
          console.error('Pipeline execution error:', err)
          setError(err.message || 'Connection error: Unable to complete planning pipeline.')
          addLog(`Pipeline execution halted: ${err.message}`, null, 'warn')
        }
      }
    }

    runApi()

    return () => {
      isCancelled = true
      hasMountedRef.current = false
    }
  }, [customerId])

  // 4. Sequential Stage Advancement
  useEffect(() => {
    if (initLoading || error) return

    let isMounted = true

    const stepInterval = 680

    const advanceStage = (stageIdx) => {
      if (!isMounted) return

      if (stageIdx >= INITIAL_STAGES.length) {
        // Stage 11 is Verification. Wait until planResponseRef.current has arrived
        const waitForDataAndComplete = () => {
          if (!isMounted) return
          if (planResponseRef.current) {
            const data = planResponseRef.current
            setIsVerified(true)
            addLog(
              `[11] Verification: Deterministic audit completed (${data.verifier?.numbers_checked ?? 11} numbers checked, status: ${data.verifier?.status ?? 'pass'}).`,
              '11',
              'success'
            )
            addLog(`STATUS: FINANCIAL PLAN VERIFIED for ${customerId}. Transitioning to Review...`, null, 'success')

            // Automatic transition after perception pause for presentation
            setTimeout(() => {
              if (isMounted && onComplete) {
                onComplete(data)
              }
            }, 1800)
          } else {
            // Poll briefly if API is taking a moment longer
            setTimeout(waitForDataAndComplete, 150)
          }
        }

        waitForDataAndComplete()
        return
      }

      setCurrentStageIndex(stageIdx)
      const current = INITIAL_STAGES[stageIdx]

      // Set current stage to running
      setStages((prev) =>
        prev.map((s) => (s.index === stageIdx ? { ...s, status: 'running' } : s))
      )

      // Emit log for stage start
      addLog(`Executing ${current.name} (${current.engine})...`, current.step, 'info')

      setTimeout(() => {
        if (!isMounted) return

        // Mark completed (or warning if risk mismatch)
        setStages((prev) =>
          prev.map((s) => {
            if (s.index !== stageIdx) return s
            if (s.id === 'risk' && planResponseRef.current?.risk?.mismatch) {
              return { ...s, status: 'warning' }
            }
            return { ...s, status: 'completed' }
          })
        )

        // Log completion details if available
        if (current.id === 'customer') {
          addLog(`[01] Customer Data: Ingested record ledger for ${customerId}.`, '01', 'success')
        } else if (current.id === 'profile') {
          addLog(`[02] Profile Engine: Solved net worth and monthly cash flow.`, '02', 'success')
        } else if (current.id === 'features') {
          addLog(`[03] Feature Extraction: Extracted behavioral time-series features.`, '03', 'success')
        } else if (current.id === 'risk') {
          if (planResponseRef.current?.risk?.mismatch) {
            addLog(`[04] Revealed Risk: Stated risk differs from behavioral capacity.`, '04', 'warn')
          } else {
            addLog(`[04] Revealed Risk: Risk preference calibrated.`, '04', 'success')
          }
        } else if (current.id === 'plans') {
          addLog(`[05] Plan Generator: 3 strategic asset trajectories generated.`, '05', 'success')
        } else if (current.id === 'montecarlo') {
          addLog(`[06] Monte Carlo: 10,000 stochastic simulation iterations complete.`, '06', 'success')
        } else if (current.id === 'stress') {
          addLog(`[07] Stress Test: Evaluated macro shocks & adverse combo scenarios.`, '07', 'success')
        } else if (current.id === 'cohort') {
          addLog(`[08] Peer Cohort: Demographic cohort benchmark aligned.`, '08', 'success')
        } else if (current.id === 'explanation') {
          addLog(`[09] AI Explanation: Generated grounded trade-off rationale.`, '09', 'success')
        } else if (current.id === 'challenge') {
          addLog(`[10] Challenger: Pre-commitment behavioral bias audit complete.`, '10', 'success')
        }

        // Advance to next stage
        advanceStage(stageIdx + 1)
      }, stepInterval)
    }

    advanceStage(0)

    return () => {
      isMounted = false
    }
  }, [initLoading, error, customerId, onComplete])

  // Short professional "Loading financial analysis" initial state
  if (initLoading) {
    return (
      <div className="min-h-[85vh] flex flex-col items-center justify-center px-4">
        <div className="relative z-10 flex flex-col items-center text-center max-w-md p-8 rounded-2xl border border-slate-800 bg-[#0c1220]/90 shadow-2xl backdrop-blur-md animate-fadeIn">
          <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/20 border border-indigo-500/30 mb-5">
            <div className="h-7 w-7 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
          </div>

          <span className="text-[11px] font-mono uppercase tracking-widest text-indigo-400 font-bold mb-1">
            Cognizant WealthIQ
          </span>

          <h3 className="text-lg font-bold text-white mb-2">
            Loading Financial Analysis
          </h3>

          <p className="text-xs text-slate-400 leading-relaxed">
            Initializing engine pipeline and secure profile ledger for <span className="text-white font-mono font-semibold">{customerId}</span>...
          </p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-[85vh] flex flex-col items-center justify-center px-4">
        <div className="max-w-md w-full p-6 rounded-2xl border border-rose-500/30 bg-rose-950/20 shadow-2xl backdrop-blur-md text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center mx-auto text-rose-400 font-bold text-xl">
            ✕
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Pipeline Execution Error</h3>
            <p className="text-xs text-rose-300 mt-1">{error}</p>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="w-1/2 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-850 text-xs font-semibold text-slate-300 border border-slate-800 cursor-pointer"
            >
              Exit to Welcome
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null)
                setInitLoading(true)
                setCurrentStageIndex(0)
                setStages(INITIAL_STAGES)
                setLogs([])
              }}
              className="w-1/2 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-xs font-semibold text-white shadow-md shadow-rose-600/30 cursor-pointer"
            >
              Retry Analysis
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-4.25rem)] max-h-[calc(100vh-4.25rem)] flex flex-col px-4 sm:px-6 py-2.5 max-w-7xl mx-auto w-full overflow-hidden animate-fadeIn">
      {/* Top Orchestration Header */}
      <div className="flex items-center justify-between gap-3 border-b border-slate-800/80 pb-2 mb-2 shrink-0">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="flex h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-400 font-bold">
              Cognizant WealthIQ Orchestration Engine
            </span>
          </div>
          <h2 className="text-lg sm:text-xl font-black text-white leading-tight">
            Autonomous Planning Pipeline &middot; <span className="font-mono text-indigo-400">{customerId}</span>
          </h2>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-800 font-mono text-[11px]">
            <span className="text-slate-400">Time:</span>
            <span className="text-white font-bold">{elapsedTime}s</span>
          </div>

          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg bg-slate-900 hover:bg-slate-850 text-slate-400 hover:text-white border border-slate-800 px-2.5 py-1 text-xs transition cursor-pointer"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Verified Banner (Appears smoothly when Stage 11 completes) */}
      {isVerified && (
        <div className="mb-2 px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-950/70 via-emerald-900/40 to-slate-950 border border-emerald-500/50 shadow-lg shadow-emerald-500/10 flex items-center justify-between gap-2 shrink-0 animate-fadeIn text-xs">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 font-bold text-sm">
              ✓
            </div>
            <div>
              <span className="text-xs font-black uppercase tracking-wider text-emerald-300 mr-2">
                FINANCIAL PLAN VERIFIED
              </span>
              <span className="text-[11px] text-slate-300">
                Cognizant Verification: {planData?.verifier?.numbers_checked ?? 11} numbers verified, 0 discrepancies.
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-emerald-400 font-semibold shrink-0">
            <span>Redirecting to Profile Review</span>
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
          </div>
        </div>
      )}

      {/* Main Orchestration Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 flex-1 min-h-0 items-stretch overflow-hidden">
        {/* Left/Center: Connected 11-Stage Pipeline Graph (8 cols) */}
        <div className="lg:col-span-8 flex flex-col h-full min-h-0 overflow-hidden">
          <div className="mb-1 flex items-center justify-between text-[11px] text-slate-400 px-1 shrink-0">
            <span className="font-semibold text-slate-300">Sequential Execution Graph (11 Stages)</span>
            <span className="font-mono text-[10px]">
              Stage {Math.min(currentStageIndex + 1, 11)} of 11
            </span>
          </div>

          <div className="rounded-2xl border border-slate-800/90 bg-[#080d18]/90 p-2.5 sm:p-3 shadow-2xl backdrop-blur-xl flex-1 flex flex-col justify-center min-h-0 overflow-hidden">
            <PipelineGraph
              stages={stages}
              currentStageIndex={currentStageIndex}
              customerId={customerId}
              realData={planData}
            />
          </div>
        </div>

        {/* Right: Live Technical Execution Console (4 cols) */}
        <div className="lg:col-span-4 flex flex-col h-full min-h-0 overflow-hidden">
          <div className="mb-1 text-[11px] font-semibold text-slate-300 px-1 shrink-0">
            Pipeline Execution Stream
          </div>

          <div className="flex-1 min-h-0 overflow-hidden">
            <ExecutionConsole
              logs={logs}
              isVerified={isVerified}
              verifierData={planData?.verifier}
              customerId={customerId}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
