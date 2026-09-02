import { useState, useEffect } from 'react'
import { fetchCustomerProfile } from '../services/api'

function formatINR(amount) {
  if (amount == null || isNaN(amount) || amount === '') return '—'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

export default function OnboardingFlow({ onComplete, onCancel, customerId, initialCustomerId = 'C001', preloadedData }) {
  const activeCustomerId = customerId || initialCustomerId || 'C001'
  const [profile, setProfile] = useState(() => {
    if (preloadedData) {
      return {
        customer_name: preloadedData.customer_name,
        customer_id: preloadedData.customer_id || activeCustomerId,
        ...preloadedData.context,
        ...preloadedData.profile,
        goals: preloadedData.goals || [],
      }
    }
    return null
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (profile) return
    let mounted = true
    const loadProfile = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const res = await fetchCustomerProfile(activeCustomerId)
        if (mounted && res) setProfile(res)
      } catch {
        if (mounted) setError(`Failed to load profile for ${activeCustomerId} from API.`)
      } finally {
        if (mounted) setIsLoading(false)
      }
    }
    loadProfile()
    return () => { mounted = false }
  }, [activeCustomerId, profile])

  const formData = profile
  const calculatedSurplus = formData ? formData.monthly_surplus : null
  const goals = formData ? (formData.goals || []) : []

  const handleFinalSubmit = () => {
    onComplete({ customer_id: activeCustomerId })
  }

  return (
    <div className="mx-auto max-w-5xl w-full py-6 px-4 sm:px-6">
      {/* Header & Exit Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-6">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
            Account Profile &middot; {activeCustomerId}
          </span>
          <h2 className="text-2xl font-black text-white mt-1">
            Review Your Financial Context &amp; Goals
          </h2>
        </div>

        <button
          type="button"
          onClick={onCancel}
          className="self-start sm:self-auto rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 px-3.5 py-1.5 text-xs transition cursor-pointer"
        >
          Exit to Welcome
        </button>
      </div>

      {/* Executive Review & Strategy Generator */}
      <div className="space-y-6 animate-fadeIn">
        <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-6 sm:p-7 shadow-xl backdrop-blur-md space-y-6">
          <div className="border-b border-slate-800/80 pb-3">
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-emerald-400">
              Review Your Profile &amp; Goals
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Confirm your parameters before the Monte Carlo simulations and adverse stress testing run.
            </p>
          </div>

          {error ? (
            <div className="p-6 text-center text-red-400 border border-red-500/20 rounded-xl bg-red-500/10">
              {error}
            </div>
          ) : !formData ? (
            <div className="p-12 flex flex-col items-center justify-center gap-3">
              {isLoading && <div className="h-6 w-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />}
              <span className="text-xs text-slate-400">Loading {activeCustomerId} profile from API...</span>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Demographics Summary */}
                <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-2 text-xs">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                    Demographics &amp; Context
                  </p>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Customer Name:</span>
                    <span className="font-semibold text-white">{formData.customer_name}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Customer ID:</span>
                    <span className="font-mono text-white">{activeCustomerId}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Age:</span>
                    <span className="font-semibold text-white">{formData.age} years</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Dependents:</span>
                    <span className="font-semibold text-white">{formData.dependents}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Employment:</span>
                    <span className="font-semibold text-white capitalize">{formData.employment_type}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">City Tier:</span>
                    <span className="font-semibold text-white capitalize">{formData.city_tier}</span>
                  </div>
                </div>

                {/* Cash Flow Summary */}
                <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-2 text-xs">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                    Monthly Cash Flow &amp; Balance Sheet
                  </p>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Monthly Income:</span>
                    <span className="font-semibold text-white">{formatINR(formData.monthly_income)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Monthly Expenses:</span>
                    <span className="font-semibold text-white">{formatINR(formData.monthly_expense)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Monthly Surplus:</span>
                    <span className={`font-bold ${
                      calculatedSurplus == null
                        ? 'text-slate-400'
                        : calculatedSurplus >= 0
                        ? 'text-emerald-400'
                        : 'text-rose-400'
                    }`}>
                      {calculatedSurplus == null
                        ? '—'
                        : calculatedSurplus < 0
                        ? `-₹${Math.abs(Math.round(calculatedSurplus)).toLocaleString('en-IN')}`
                        : `+${formatINR(calculatedSurplus)}`}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Net Worth:</span>
                    <span className="font-semibold text-white">{formatINR(formData.net_worth)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Emergency Fund:</span>
                    <span className="font-semibold text-white">{formData.emergency_fund_months}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Stated Risk Preference:</span>
                    <span className="font-semibold text-amber-300 capitalize">{formData.stated_risk}</span>
                  </div>
                </div>
              </div>

              {/* Planned Goals Review */}
              <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 text-xs">
                <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 mb-2.5">
                  Planned Financial Goals ({goals.length})
                </p>
                <div className="space-y-2">
                  {goals.map((g, idx) => {
                    return (
                      <div
                        key={g.id || idx}
                        className="flex items-center justify-between py-2 border-b border-slate-800/60 last:border-0"
                      >
                        <div className="flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded bg-slate-800 text-[10px] font-bold text-white border border-slate-700">
                            #{g.priority}
                          </span>
                          <span className="text-white font-medium capitalize">
                            {g.name ? g.name.replace(/_/g, ' ') : ''}
                          </span>
                        </div>
                        <span className="text-emerald-400 font-bold">
                          {formatINR(g.target_amount)} <span className="text-slate-400 font-normal">in {g.years} years</span>
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Review Action Buttons */}
        <div className="pt-2 flex items-center justify-between">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 px-5 py-2.5 text-xs font-semibold transition cursor-pointer"
          >
            &larr; Exit to Welcome
          </button>

          <button
            type="button"
            disabled={!formData}
            onClick={handleFinalSubmit}
            className="rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition cursor-pointer flex items-center justify-center gap-2"
          >
            <span>Generate Financial Strategies</span>
            <span>&rarr;</span>
          </button>
        </div>
      </div>
    </div>
  )
}
