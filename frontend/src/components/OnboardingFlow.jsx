import { useState, useEffect } from 'react'
import { fetchCustomerProfile } from '../services/api'

function formatINR(amount) {
  if (amount == null || isNaN(amount) || amount === '') return '₹0'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

const AVAILABLE_CUSTOMERS = ['C001', 'C002', 'C003'];

export default function OnboardingFlow({ onComplete, onCancel }) {
  const [currentStep, setCurrentStep] = useState(1)
  const [selectedCustomerId, setSelectedCustomerId] = useState('C001')
  const [profiles, setProfiles] = useState({})
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let mounted = true
    const loadAll = async () => {
      setIsLoading(true)
      setError(null)
      const data = {}
      try {
        for (const id of AVAILABLE_CUSTOMERS) {
          const res = await fetchCustomerProfile(id)
          if (res) data[id] = res
        }
        if (mounted) setProfiles(data)
      } catch (err) {
        if (mounted) setError("Failed to load customer profiles from API.")
      } finally {
        if (mounted) setIsLoading(false)
      }
    }
    loadAll()
    return () => { mounted = false }
  }, [])

  const formData = profiles[selectedCustomerId]
  
  const calculatedSurplus = formData ? (formData.monthly_surplus || 0) : 0;
  const goals = formData ? (formData.goals || []) : [];

  const handleFinalSubmit = () => {
    // Only send what the backend contract strictly expects
    onComplete({ customer_id: selectedCustomerId })
  }

  const steps = [
    { num: 1, label: 'Select Demo Persona' },
    { num: 2, label: 'Review & Run' },
  ]

  return (
    <div className="mx-auto max-w-5xl w-full py-6 px-4 sm:px-6">
      {/* Header & Exit Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-6">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
            Step {currentStep} of 2 &middot; {currentStep === 1 ? 'Select Demo Persona' : 'Review & Run'}
          </span>
          <h2 className="text-2xl font-black text-white mt-1">
            Explore Engine Capabilities
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

      {/* Stepper Progress Indicator */}
      <div className="grid grid-cols-2 gap-3 mb-8">
        {steps.map((s) => (
          <div key={s.num} className="flex flex-col items-center gap-1.5">
            <div
              className={`h-1.5 w-full rounded-full transition-all duration-300 ${
                currentStep >= s.num
                  ? 'bg-indigo-500 shadow-sm shadow-indigo-500/50'
                  : 'bg-slate-800'
              }`}
            />
            <span
              className={`text-xs font-medium transition-colors ${
                currentStep === s.num
                  ? 'text-indigo-400 font-bold'
                  : currentStep > s.num
                  ? 'text-slate-300'
                  : 'text-slate-400'
              }`}
            >
              {s.label}
            </span>
          </div>
        ))}
      </div>

      {/* STEP 1: Persona Selection */}
      {currentStep === 1 && (
        <div className="space-y-6 animate-fadeIn">
          <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-6 sm:p-7 shadow-xl backdrop-blur-md">
            <div className="mb-6 border-b border-slate-800/80 pb-4">
              <h3 className="text-lg font-bold text-white">Select a Demo Persona</h3>
              <p className="text-xs text-slate-400 mt-1">
                Choose one of the predefined personas to explore the financial planning engine's capabilities.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {AVAILABLE_CUSTOMERS.map((id) => {
                const profile = profiles[id];
                return (
                <button
                  key={id}
                  onClick={() => setSelectedCustomerId(id)}
                  className={`text-left p-5 rounded-xl border transition-all duration-200 cursor-pointer ${
                    selectedCustomerId === id
                      ? 'bg-indigo-600/10 border-indigo-500 ring-1 ring-indigo-500/50'
                      : 'bg-slate-900/50 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-mono text-[10px] text-indigo-400 font-bold px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20">
                      {id}
                    </span>
                  </div>
                  <h4 className="text-white font-bold text-base mb-1">{profile ? profile.customer_name : 'Loading...'}</h4>
                  {profile ? (
                  <div className="space-y-1 mt-3">
                    <p className="text-xs text-slate-400 flex justify-between">
                      <span>Age:</span> <span className="text-slate-300">{profile.age}</span>
                    </p>
                    <p className="text-xs text-slate-400 flex justify-between">
                      <span>Employment:</span> <span className="text-slate-300 capitalize">{profile.employment_type.replace('_', ' ')}</span>
                    </p>
                    <p className="text-xs text-slate-400 flex justify-between">
                      <span>Risk:</span> <span className="text-amber-400 capitalize">{profile.stated_risk}</span>
                    </p>
                    <p className="text-xs text-slate-400 flex justify-between">
                      <span>Goals:</span> <span className="text-emerald-400">{profile.goals.length}</span>
                    </p>
                  </div>
                  ) : (
                  <div className="space-y-1 mt-3">
                    <p className="text-xs text-slate-400">Fetching API data...</p>
                  </div>
                  )}
                </button>
                )
              })}
            </div>

            <div className="pt-8 flex justify-end">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 transition cursor-pointer"
              >
                <span>Continue to Review</span>
                <span>&rarr;</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: Executive Review & Strategy Generator */}
      {currentStep === 2 && (
        <div className="space-y-6 animate-fadeIn">
          <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-6 sm:p-7 shadow-xl backdrop-blur-md space-y-6">
            <div className="border-b border-slate-800/80 pb-3">
              <h3 className="text-sm font-extrabold uppercase tracking-wider text-emerald-400">
                Review Your Profile &amp; Goals
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Confirm your parameters before initiating the 10,000 Monte Carlo simulations and adverse stress testing.
              </p>
            </div>
            
            {error ? (
              <div className="p-6 text-center text-red-400 border border-red-500/20 rounded-xl bg-red-500/10">
                {error}
              </div>
            ) : !formData ? (
              <div className="p-10 flex justify-center">
                <span className="text-slate-400 animate-pulse">Loading profile from API...</span>
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
                  <span className="font-mono text-white">{selectedCustomerId}</span>
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
                  <span className={`font-bold ${calculatedSurplus >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {calculatedSurplus < 0
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

          {/* Review Stepper Navigation */}
          <div className="pt-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 px-5 py-2.5 text-xs font-semibold transition cursor-pointer"
            >
              &larr; Back to Selection
            </button>

            <button
              type="button"
              onClick={handleFinalSubmit}
              className="rounded-xl bg-emerald-600 hover:bg-emerald-500 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition cursor-pointer flex items-center justify-center gap-2"
            >
              <span>Generate Financial Strategies</span>
              <span>&rarr;</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
