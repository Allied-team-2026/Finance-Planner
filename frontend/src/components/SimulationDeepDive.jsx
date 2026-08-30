import { useState } from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts'

function formatLakhs(val) {
  if (val == null || isNaN(val)) return '—'
  return `₹${(val / 100000).toFixed(1)}L`
}

function CustomTooltip({ active, payload, label, goalAmount }) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-3.5 shadow-xl backdrop-blur-md text-xs">
        <p className="font-bold text-white mb-2">{label}</p>
        {payload.map((entry, index) => (
          <div key={`item-${index}`} className="flex items-center justify-between gap-4 py-0.5">
            <span className="flex items-center gap-1.5 text-slate-300">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: entry.color }} />
              {entry.name}:
            </span>
            <span className="font-semibold text-white">
              {entry.value == null ? '—' : `₹${entry.value.toLocaleString('en-IN')}`}
            </span>
          </div>
        ))}
        <div className="mt-2 pt-2 border-t border-slate-800 flex justify-between text-[11px] text-slate-400">
          <span>Goal Target:</span>
          <span className="font-medium text-emerald-400">
            {goalAmount == null ? '—' : `₹${goalAmount.toLocaleString('en-IN')}`}
          </span>
        </div>
      </div>
    )
  }
  return null
}

export default function SimulationDeepDive({ plans, goalAmount, nSimulations }) {
  const [isOpen, setIsOpen] = useState(false)

  if (!plans || plans.length === 0) return null

  const chartData = plans.map((p) => ({
    name: `Plan ${p.plan_id} (${p.label})`,
    '10th Percentile Outcome (P10)': p.p10_corpus,
    '50th Percentile Outcome (Median)': p.median_corpus,
    '90th Percentile Outcome (P90)': p.p90_corpus,
    plan_id: p.plan_id,
    feasible: p.feasible,
    survives_stress: p.survives_stress,
  }))

  return (
    <div className="rounded-2xl border border-slate-800/80 bg-gradient-to-b from-[#101726]/80 to-[#0a0e18]/80 p-5 backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 3v18h18" />
              <path d="m19 9-5 5-4-4-3 3" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white">Monte Carlo Simulation Distribution</h3>
              <span className="rounded bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/20">
                {nSimulations == null ? 'Historical runs' : `${nSimulations.toLocaleString('en-IN')} historical runs`}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Compare outcome distribution across the 10th percentile outcome (P10), median (50th percentile), and 90th percentile outcome (P90).
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 border border-slate-700 transition cursor-pointer"
        >
          <span>{isOpen ? 'Collapse Simulation Graph' : 'Expand Simulation Graph'}</span>
          <svg
            className={`h-3.5 w-3.5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      </div>

      {isOpen && (
        <div className="mt-5 pt-4 border-t border-slate-800/80 animate-fadeIn">
          <div className="h-72 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 10, bottom: 5 }}
              >
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  axisLine={{ stroke: '#334155' }}
                />
                <YAxis
                  tickFormatter={formatLakhs}
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={{ stroke: '#334155' }}
                />
                <Tooltip content={<CustomTooltip goalAmount={goalAmount} />} />
                <Legend
                  wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                />
                {goalAmount != null && (
                  <ReferenceLine
                    y={goalAmount}
                    stroke="#10b981"
                    strokeDasharray="4 4"
                    label={{
                      value: `Goal Target: ${formatLakhs(goalAmount)}`,
                      fill: '#10b981',
                      fontSize: 11,
                      position: 'top',
                    }}
                  />
                )}
                <Bar
                  dataKey="10th Percentile Outcome (P10)"
                  fill="#64748b"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="50th Percentile Outcome (Median)"
                  fill="#6366f1"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="90th Percentile Outcome (P90)"
                  fill="#38bdf8"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* One line per plan, generated from that plan's own numbers. The old
              version had this text hardcoded, so it described plan A of customer
              C001 no matter whose screen it was. */}
          <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-400 bg-slate-950/40 p-3 rounded-xl border border-slate-800/80">
            {plans.map((p) => (
              <div key={p.plan_id}>
                <strong className={p.feasible ? 'text-white' : 'text-rose-400'}>
                  Plan {p.plan_id} ({p.label}):
                </strong>{' '}
                worst case (P10) {formatLakhs(p.p10_corpus)}, median {formatLakhs(p.median_corpus)}.
                {p.p10_gap_to_goal > 0 && ` ${formatLakhs(p.p10_gap_to_goal)} short of the goal at P10.`}
                {!p.feasible && ' Not affordable on your current surplus.'}
                {p.exceeds_risk_ceiling && ' Above your risk level.'}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
