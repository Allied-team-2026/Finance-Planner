import { useState } from 'react'

function formatINR(amount) {
  if (amount == null || isNaN(amount) || amount === '') return '₹0'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

const GOAL_TYPE_OPTIONS = [
  { value: 'house_downpayment', label: 'House Downpayment' },
  { value: 'child_education', label: 'Child Education' },
  { value: 'retirement', label: 'Retirement' },
  { value: 'vehicle', label: 'Vehicle' },
  { value: 'emergency_fund', label: 'Emergency Fund' },
  { value: 'custom', label: 'Custom Goal' },
]

const EMERGENCY_FUND_OPTIONS = [
  'Less than 1 month',
  '1 month',
  '2 months',
  '3 months',
  '4 months',
  '5 months',
  '6 months',
  'More than 6 months',
]

const EMPTY_PROFILE = {
  customer_name: '',
  customer_id: '',
  age: '',
  dependents: '',
  employment_type: '',
  city_tier: '',
  monthly_income: '',
  monthly_expense: '',
  net_worth: '',
  existing_emi_total: '',
  emergency_fund_months: '',
  stated_risk: 'moderate',
}

export default function OnboardingFlow({ onComplete, onCancel }) {
  const [currentStep, setCurrentStep] = useState(1) // 1: Profile & Goals, 2: Risk Profile, 3: Review
  const [formData, setFormData] = useState({ ...EMPTY_PROFILE })
  const [goals, setGoals] = useState([
    {
      id: 'g-1',
      goal_type: 'house_downpayment',
      custom_name: '',
      target_amount: '',
      years: '',
      priority: 1,
    },
  ])
  const [errors, setErrors] = useState({})

  // Handle Form Change for Profile
  const handleProfileChange = (e) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value,
    }))
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }))
    }
  }

  // Calculated Surplus
  const incomeNum = formData.monthly_income === '' ? 0 : Number(formData.monthly_income)
  const expenseNum = formData.monthly_expense === '' ? 0 : Number(formData.monthly_expense)
  const hasIncomeOrExpense = formData.monthly_income !== '' || formData.monthly_expense !== ''
  const calculatedSurplus = incomeNum - expenseNum

  // Goals Management
  const handleGoalChange = (id, field, value) => {
    setGoals((prev) =>
      prev.map((g) => {
        if (g.id === id) {
          return {
            ...g,
            [field]: field === 'target_amount' || field === 'years' || field === 'priority'
              ? (value === '' ? '' : Number(value))
              : value,
          }
        }
        return g
      })
    )
    if (errors[`goal-${id}-${field}`] || errors.goals) {
      setErrors((prev) => ({ ...prev, [`goal-${id}-${field}`]: null, goals: null }))
    }
  }

  const handleAddGoal = () => {
    const nextPriority = goals.length < 5 ? goals.length + 1 : 5
    const newGoal = {
      id: `g-${Date.now()}`,
      goal_type: 'child_education',
      custom_name: '',
      target_amount: '',
      years: '',
      priority: nextPriority,
    }
    setGoals((prev) => [...prev, newGoal])
    if (errors.goals) {
      setErrors((prev) => ({ ...prev, goals: null }))
    }
  }

  const handleRemoveGoal = (id) => {
    setGoals((prev) => prev.filter((g) => g.id !== id))
  }

  // Validate Step 1 (Financial Profile & Goals)
  const validateStep1 = () => {
    const errs = {}

    if (!formData.customer_name.trim()) {
      errs.customer_name = 'Customer name is required'
    }
    if (formData.age === '' || Number(formData.age) <= 0 || Number(formData.age) > 110) {
      errs.age = 'Enter a valid age between 18 and 100'
    }
    if (!formData.employment_type) {
      errs.employment_type = 'Select an employment type'
    }
    if (!formData.city_tier) {
      errs.city_tier = 'Select a city tier'
    }
    if (formData.monthly_income === '' || Number(formData.monthly_income) < 0) {
      errs.monthly_income = 'Enter a valid monthly income (>= 0)'
    }
    if (formData.monthly_expense === '' || Number(formData.monthly_expense) < 0) {
      errs.monthly_expense = 'Enter a valid monthly expense (>= 0)'
    }

    if (goals.length === 0) {
      errs.goals = 'At least one financial goal is required'
    } else {
      goals.forEach((g) => {
        if (g.goal_type === 'custom' && !g.custom_name.trim()) {
          errs[`goal-${g.id}-custom_name`] = 'Goal name is required'
        }
        if (g.target_amount === '' || Number(g.target_amount) <= 0) {
          errs[`goal-${g.id}-target_amount`] = 'Enter a target amount > 0'
        }
        if (g.years === '' || Number(g.years) <= 0) {
          errs[`goal-${g.id}-years`] = 'Enter timeline in years (> 0)'
        }
      })
    }

    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleContinueToRisk = (e) => {
    e.preventDefault()
    if (validateStep1()) {
      setCurrentStep(2)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // Final Submission to API
  const handleFinalSubmit = () => {
    const payload = {
      customer_name: formData.customer_name.trim() || 'Customer',
      customer_id: formData.customer_id.trim() || `C-${Math.floor(100 + Math.random() * 900)}`,
      age: Number(formData.age),
      dependents: formData.dependents === '' ? 0 : Number(formData.dependents),
      employment_type: formData.employment_type || 'salaried',
      city_tier: formData.city_tier || 'metro',
      monthly_income: Number(formData.monthly_income),
      monthly_expense: Number(formData.monthly_expense),
      monthly_surplus: calculatedSurplus,
      net_worth: Number(formData.net_worth || 0),
      assets: Number(formData.net_worth || 0),
      liabilities: Number(formData.existing_emi_total || 0),
      existing_emi_total: Number(formData.existing_emi_total || 0),
      emergency_fund_months: formData.emergency_fund_months || '3 months',
      savings_account: Number(formData.monthly_expense || 0) * 3,
      stated_risk: formData.stated_risk || 'moderate',
      goals: goals.map((g, idx) => {
        const isCustom = g.goal_type === 'custom'
        const displayName = isCustom ? (g.custom_name?.trim() || 'Custom Goal') : (GOAL_TYPE_OPTIONS.find((o) => o.value === g.goal_type)?.label || g.goal_type)
        const rawName = isCustom ? displayName.toLowerCase().replace(/\s+/g, '_') : g.goal_type
        return {
          name: rawName,
          displayName: displayName,
          target_amount: Number(g.target_amount),
          years: Number(g.years),
          priority: Number(g.priority || idx + 1),
        }
      }),
    }

    onComplete(payload)
  }

  const steps = [
    { num: 1, label: 'Profile & Goals' },
    { num: 2, label: 'Risk Preference' },
    { num: 3, label: 'Review & Run' },
  ]

  return (
    <div className="mx-auto max-w-5xl w-full py-6 px-4 sm:px-6">
      {/* Header & Exit Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-6">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
            Step {currentStep} of 3 &middot; Onboarding Questionnaire
          </span>
          <h2 className="text-2xl font-black text-white mt-1">
            Build your personalized financial baseline
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
      <div className="grid grid-cols-3 gap-3 mb-8">
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
              {s.num}. {s.label}
            </span>
          </div>
        ))}
      </div>

      {/* STEP 1: Two-Column FINANCIAL PROFILE & Structured FINANCIAL GOALS Table */}
      {currentStep === 1 && (
        <form onSubmit={handleContinueToRisk} className="space-y-8 animate-fadeIn">
          {/* SECTION 1: FINANCIAL PROFILE PANEL (2 Columns) */}
          <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-6 sm:p-7 shadow-xl backdrop-blur-md space-y-6">
            <div className="border-b border-slate-800/80 pb-3">
              <h3 className="text-sm font-extrabold uppercase tracking-wider text-indigo-400">
                Financial Profile
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Enter your demographic context, balance sheet, and monthly cash flow baseline.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* LEFT COLUMN: Demographics & Identity */}
              <div className="space-y-4 text-xs">
                {/* 1. Customer Name */}
                <div>
                  <label htmlFor="customer_name" className="block font-semibold text-slate-300 mb-1">
                    Customer Name <span className="text-rose-400">*</span>
                  </label>
                  <input
                    id="customer_name"
                    type="text"
                    name="customer_name"
                    value={formData.customer_name}
                    onChange={handleProfileChange}
                    placeholder="Enter customer name"
                    className={`w-full rounded-xl bg-slate-950 border px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 ${
                      errors.customer_name
                        ? 'border-rose-500/70 focus:ring-rose-500'
                        : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                    }`}
                  />
                  {errors.customer_name && (
                    <p className="mt-1 text-[11px] text-rose-400">{errors.customer_name}</p>
                  )}
                </div>

                {/* 2. Customer ID */}
                <div>
                  <label htmlFor="customer_id" className="block font-semibold text-slate-300 mb-1">
                    Customer ID
                  </label>
                  <input
                    id="customer_id"
                    type="text"
                    name="customer_id"
                    value={formData.customer_id}
                    onChange={handleProfileChange}
                    placeholder="Enter customer ID"
                    className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 font-mono"
                  />
                </div>

                {/* 3. Age */}
                <div>
                  <label htmlFor="age" className="block font-semibold text-slate-300 mb-1">
                    Age <span className="text-rose-400">*</span>
                  </label>
                  <input
                    id="age"
                    type="number"
                    name="age"
                    min="18"
                    max="100"
                    value={formData.age}
                    onChange={handleProfileChange}
                    placeholder="Enter age"
                    className={`w-full rounded-xl bg-slate-950 border px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 ${
                      errors.age
                        ? 'border-rose-500/70 focus:ring-rose-500'
                        : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                    }`}
                  />
                  {errors.age && (
                    <p className="mt-1 text-[11px] text-rose-400">{errors.age}</p>
                  )}
                </div>

                {/* 4. Dependents */}
                <div>
                  <label htmlFor="dependents" className="block font-semibold text-slate-300 mb-1">
                    Dependents
                  </label>
                  <input
                    id="dependents"
                    type="number"
                    name="dependents"
                    min="0"
                    max="10"
                    value={formData.dependents}
                    onChange={handleProfileChange}
                    placeholder="Number of dependents"
                    className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                {/* 5. Employment Type */}
                <div>
                  <label htmlFor="employment_type" className="block font-semibold text-slate-300 mb-1">
                    Employment Type <span className="text-rose-400">*</span>
                  </label>
                  <select
                    id="employment_type"
                    name="employment_type"
                    value={formData.employment_type}
                    onChange={handleProfileChange}
                    className={`w-full rounded-xl bg-slate-950 border px-3.5 py-2.5 text-xs text-white focus:outline-none focus:ring-1 cursor-pointer ${
                      errors.employment_type
                        ? 'border-rose-500/70 focus:ring-rose-500'
                        : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                    }`}
                  >
                    <option value="">Select employment type</option>
                    <option value="salaried">Salaried</option>
                    <option value="self_employed">Self-employed</option>
                    <option value="business_owner">Business owner</option>
                  </select>
                  {errors.employment_type && (
                    <p className="mt-1 text-[11px] text-rose-400">{errors.employment_type}</p>
                  )}
                </div>

                {/* 6. City Tier */}
                <div>
                  <label htmlFor="city_tier" className="block font-semibold text-slate-300 mb-1">
                    City Tier <span className="text-rose-400">*</span>
                  </label>
                  <select
                    id="city_tier"
                    name="city_tier"
                    value={formData.city_tier}
                    onChange={handleProfileChange}
                    className={`w-full rounded-xl bg-slate-950 border px-3.5 py-2.5 text-xs text-white focus:outline-none focus:ring-1 cursor-pointer ${
                      errors.city_tier
                        ? 'border-rose-500/70 focus:ring-rose-500'
                        : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                    }`}
                  >
                    <option value="">Select city tier</option>
                    <option value="metro">Metro</option>
                    <option value="tier_2">Tier 2</option>
                    <option value="tier_3">Tier 3</option>
                  </select>
                  {errors.city_tier && (
                    <p className="mt-1 text-[11px] text-rose-400">{errors.city_tier}</p>
                  )}
                </div>
              </div>

              {/* RIGHT COLUMN: Financial Cash Flow & Assets */}
              <div className="space-y-4 text-xs">
                {/* 7. Monthly Income */}
                <div>
                  <label htmlFor="monthly_income" className="block font-semibold text-slate-300 mb-1">
                    Monthly Income <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
                    <input
                      id="monthly_income"
                      type="number"
                      name="monthly_income"
                      step="1000"
                      min="0"
                      value={formData.monthly_income}
                      onChange={handleProfileChange}
                      placeholder="Monthly income"
                      className={`w-full rounded-xl bg-slate-950 border pl-8 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 ${
                        errors.monthly_income
                          ? 'border-rose-500/70 focus:ring-rose-500'
                          : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                      }`}
                    />
                  </div>
                  {errors.monthly_income && (
                    <p className="mt-1 text-[11px] text-rose-400">{errors.monthly_income}</p>
                  )}
                </div>

                {/* 8. Monthly Expense */}
                <div>
                  <label htmlFor="monthly_expense" className="block font-semibold text-slate-300 mb-1">
                    Monthly Expense <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
                    <input
                      id="monthly_expense"
                      type="number"
                      name="monthly_expense"
                      step="1000"
                      min="0"
                      value={formData.monthly_expense}
                      onChange={handleProfileChange}
                      placeholder="Monthly expense"
                      className={`w-full rounded-xl bg-slate-950 border pl-8 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 ${
                        errors.monthly_expense
                          ? 'border-rose-500/70 focus:ring-rose-500'
                          : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                      }`}
                    />
                  </div>
                  {errors.monthly_expense && (
                    <p className="mt-1 text-[11px] text-rose-400">{errors.monthly_expense}</p>
                  )}
                </div>

                {/* 9. Monthly Surplus (READ-ONLY Auto-Calculated) */}
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">
                    Monthly Surplus — Auto Calculated
                  </label>
                  <div className="w-full rounded-xl bg-[#090e1a] border border-slate-800 px-3.5 py-2.5 flex items-center justify-between">
                    <span className="text-slate-400 text-xs">Income &minus; Expense:</span>
                    <span className={`text-sm font-bold ${
                      hasIncomeOrExpense
                        ? calculatedSurplus >= 0
                          ? 'text-emerald-400'
                          : 'text-rose-400'
                        : 'text-slate-400'
                    }`}>
                      {hasIncomeOrExpense
                        ? calculatedSurplus < 0
                          ? `-₹${Math.abs(Math.round(calculatedSurplus)).toLocaleString('en-IN')}`
                          : `₹${Math.round(calculatedSurplus).toLocaleString('en-IN')}`
                        : '₹0'}
                    </span>
                  </div>
                  <p className="mt-1 text-[10px] text-slate-400">
                    Calculated automatically from monthly income and expenses.
                  </p>
                </div>

                {/* 10. Net Worth */}
                <div>
                  <label htmlFor="net_worth" className="block font-semibold text-slate-300 mb-1">
                    Net Worth
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
                    <input
                      id="net_worth"
                      type="number"
                      name="net_worth"
                      step="10000"
                      value={formData.net_worth}
                      onChange={handleProfileChange}
                      placeholder="Current net worth"
                      className="w-full rounded-xl bg-slate-950 border border-slate-800 pl-8 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </div>

                {/* 11. Existing EMI / Liabilities */}
                <div>
                  <label htmlFor="existing_emi_total" className="block font-semibold text-slate-300 mb-1">
                    Existing EMI / Liabilities
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
                    <input
                      id="existing_emi_total"
                      type="number"
                      name="existing_emi_total"
                      step="1000"
                      value={formData.existing_emi_total}
                      onChange={handleProfileChange}
                      placeholder="Monthly EMI / liabilities"
                      className="w-full rounded-xl bg-slate-950 border border-slate-800 pl-8 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </div>

                {/* 12. Emergency Fund */}
                <div>
                  <label htmlFor="emergency_fund_months" className="block font-semibold text-slate-300 mb-1">
                    Emergency Fund
                  </label>
                  <select
                    id="emergency_fund_months"
                    name="emergency_fund_months"
                    value={formData.emergency_fund_months}
                    onChange={handleProfileChange}
                    className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
                  >
                    <option value="">Select months</option>
                    {EMERGENCY_FUND_OPTIONS.map((opt, idx) => (
                      <option key={idx} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 2: FINANCIAL GOALS TABLE */}
          <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-6 sm:p-7 shadow-xl backdrop-blur-md space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
              <div>
                <h3 className="text-sm font-extrabold uppercase tracking-wider text-emerald-400">
                  Financial Goals
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Define your targeted financial goals, capital requirements, timelines, and execution priorities.
                </p>
              </div>

              <button
                type="button"
                onClick={handleAddGoal}
                className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600/90 hover:bg-indigo-500 px-3.5 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/25 transition cursor-pointer self-start sm:self-auto"
              >
                <span>+ Add Another Goal</span>
              </button>
            </div>

            {errors.goals && (
              <p className="text-xs text-rose-400 font-medium">{errors.goals}</p>
            )}

            {/* Structured Table Layout for Goals */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                    <th className="pb-3 pr-3 font-semibold">Goal Type</th>
                    <th className="pb-3 pr-3 font-semibold">Target Amount</th>
                    <th className="pb-3 pr-3 font-semibold">Timeline</th>
                    <th className="pb-3 pr-3 font-semibold">Priority</th>
                    <th className="pb-3 font-semibold text-center w-16">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {goals.map((goal) => (
                    <tr key={goal.id} className="align-top">
                      {/* Goal Type & Custom Name Input */}
                      <td className="py-3.5 pr-3">
                        <div className="space-y-2">
                          <select
                            value={goal.goal_type}
                            onChange={(e) => handleGoalChange(goal.id, 'goal_type', e.target.value)}
                            className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer min-w-[170px]"
                          >
                            {GOAL_TYPE_OPTIONS.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>

                          {/* Custom Goal Name Input (Visible only if 'custom' is selected) */}
                          {goal.goal_type === 'custom' && (
                            <div>
                              <input
                                type="text"
                                value={goal.custom_name}
                                onChange={(e) => handleGoalChange(goal.id, 'custom_name', e.target.value)}
                                placeholder="Enter goal name (e.g. Wedding)"
                                className={`w-full rounded-xl bg-slate-950 border px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 ${
                                  errors[`goal-${goal.id}-custom_name`]
                                    ? 'border-rose-500/70 focus:ring-rose-500'
                                    : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                                }`}
                              />
                              {errors[`goal-${goal.id}-custom_name`] && (
                                <p className="mt-1 text-[10px] text-rose-400">{errors[`goal-${goal.id}-custom_name`]}</p>
                              )}
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Target Amount */}
                      <td className="py-3.5 pr-3">
                        <div className="relative min-w-[140px]">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-xs">₹</span>
                          <input
                            type="number"
                            step="50000"
                            min="1"
                            value={goal.target_amount}
                            onChange={(e) => handleGoalChange(goal.id, 'target_amount', e.target.value)}
                            placeholder="Target amount"
                            className={`w-full rounded-xl bg-slate-950 border pl-7 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 ${
                              errors[`goal-${goal.id}-target_amount`]
                                ? 'border-rose-500/70 focus:ring-rose-500'
                                : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                            }`}
                          />
                        </div>
                        {errors[`goal-${goal.id}-target_amount`] && (
                          <p className="mt-1 text-[10px] text-rose-400">{errors[`goal-${goal.id}-target_amount`]}</p>
                        )}
                      </td>

                      {/* Timeline (Years) */}
                      <td className="py-3.5 pr-3">
                        <div className="min-w-[100px]">
                          <input
                            type="number"
                            min="1"
                            max="40"
                            value={goal.years}
                            onChange={(e) => handleGoalChange(goal.id, 'years', e.target.value)}
                            placeholder="Years"
                            className={`w-full rounded-xl bg-slate-950 border px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 ${
                              errors[`goal-${goal.id}-years`]
                                ? 'border-rose-500/70 focus:ring-rose-500'
                                : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500'
                            }`}
                          />
                        </div>
                        {errors[`goal-${goal.id}-years`] && (
                          <p className="mt-1 text-[10px] text-rose-400">{errors[`goal-${goal.id}-years`]}</p>
                        )}
                      </td>

                      {/* Priority */}
                      <td className="py-3.5 pr-3">
                        <select
                          value={goal.priority}
                          onChange={(e) => handleGoalChange(goal.id, 'priority', e.target.value)}
                          className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer min-w-[110px]"
                        >
                          <option value="1">Priority 1</option>
                          <option value="2">Priority 2</option>
                          <option value="3">Priority 3</option>
                          <option value="4">Priority 4</option>
                          <option value="5">Priority 5</option>
                        </select>
                      </td>

                      {/* Remove Action */}
                      <td className="py-3.5 text-center align-middle">
                        {goals.length > 1 ? (
                          <button
                            type="button"
                            onClick={() => handleRemoveGoal(goal.id)}
                            className="rounded-lg p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition cursor-pointer"
                            title="Remove goal"
                          >
                            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="3 6 5 6 21 6" />
                              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                            </svg>
                          </button>
                        ) : (
                          <span className="text-slate-600 text-xs">&mdash;</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Form Action Controls */}
          <div className="pt-2 flex items-center justify-between">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 px-5 py-2.5 text-xs font-semibold transition cursor-pointer"
            >
              Cancel
            </button>

            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 transition cursor-pointer"
            >
              <span>Continue to Risk Profile</span>
              <span>&rarr;</span>
            </button>
          </div>
        </form>
      )}

      {/* STEP 2: Stated Risk Preference */}
      {currentStep === 2 && (
        <div className="space-y-6 animate-fadeIn">
          <div className="rounded-2xl border border-slate-800 bg-[#0d1322]/95 p-6 sm:p-7 shadow-xl backdrop-blur-md space-y-6">
            <div className="border-b border-slate-800/80 pb-3">
              <h3 className="text-sm font-extrabold uppercase tracking-wider text-indigo-400">
                Stated Risk Preference
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Select your comfort level with market volatility and drawdown fluctuations.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Conservative */}
              <button
                type="button"
                onClick={() => setFormData((p) => ({ ...p, stated_risk: 'conservative' }))}
                className={`rounded-2xl p-5 border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between ${
                  formData.stated_risk === 'conservative'
                    ? 'border-indigo-500 bg-indigo-950/20 ring-1 ring-indigo-500 shadow-md'
                    : 'border-slate-800 bg-[#090e1a] hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-white capitalize">Conservative</span>
                    {formData.stated_risk === 'conservative' && (
                      <span className="h-2 w-2 rounded-full bg-indigo-400" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-snug">
                    Priority on capital preservation and debt stability. Lower volatility tolerance.
                  </p>
                </div>
                <span className="mt-4 text-[10px] font-semibold text-slate-400 uppercase">
                  Lower Equity Exposure
                </span>
              </button>

              {/* Moderate */}
              <button
                type="button"
                onClick={() => setFormData((p) => ({ ...p, stated_risk: 'moderate' }))}
                className={`rounded-2xl p-5 border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between ${
                  formData.stated_risk === 'moderate'
                    ? 'border-indigo-500 bg-indigo-950/20 ring-1 ring-indigo-500 shadow-md'
                    : 'border-slate-800 bg-[#090e1a] hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-white capitalize">Moderate</span>
                    {formData.stated_risk === 'moderate' && (
                      <span className="h-2 w-2 rounded-full bg-indigo-400" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-snug">
                    Balanced allocation between equity growth and debt resilience over a 5-10 year horizon.
                  </p>
                </div>
                <span className="mt-4 text-[10px] font-semibold text-indigo-400 uppercase">
                  Balanced Mix
                </span>
              </button>

              {/* Aggressive */}
              <button
                type="button"
                onClick={() => setFormData((p) => ({ ...p, stated_risk: 'aggressive' }))}
                className={`rounded-2xl p-5 border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between ${
                  formData.stated_risk === 'aggressive'
                    ? 'border-indigo-500 bg-indigo-950/20 ring-1 ring-indigo-500 shadow-md'
                    : 'border-slate-800 bg-[#090e1a] hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-white capitalize">Aggressive</span>
                    {formData.stated_risk === 'aggressive' && (
                      <span className="h-2 w-2 rounded-full bg-indigo-400" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-snug">
                    High growth focus with higher equity allocation. Willing to ride through market drawdowns.
                  </p>
                </div>
                <span className="mt-4 text-[10px] font-semibold text-cyan-400 uppercase">
                  High Growth Orientation
                </span>
              </button>
            </div>
          </div>

          {/* Stepper Navigation */}
          <div className="pt-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 px-5 py-2.5 text-xs font-semibold transition cursor-pointer"
            >
              &larr; Back to Profile &amp; Goals
            </button>

            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 transition cursor-pointer"
            >
              <span>Continue to Review</span>
              <span>&rarr;</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Executive Review & Strategy Generator */}
      {currentStep === 3 && (
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Demographics Summary */}
              <div className="rounded-xl bg-[#090e1a] p-4 border border-slate-800 space-y-2 text-xs">
                <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                  Demographics &amp; Context
                </p>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Customer Name:</span>
                  <span className="font-semibold text-white">{formData.customer_name || 'Customer'}</span>
                </div>
                {formData.customer_id && (
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Customer ID:</span>
                    <span className="font-mono text-white">{formData.customer_id}</span>
                  </div>
                )}
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Age:</span>
                  <span className="font-semibold text-white">{formData.age} years</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Dependents:</span>
                  <span className="font-semibold text-white">{formData.dependents || '0'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Employment:</span>
                  <span className="font-semibold text-white capitalize">{formData.employment_type || 'Salaried'}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">City Tier:</span>
                  <span className="font-semibold text-white capitalize">{formData.city_tier || 'Metro'}</span>
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
                {formData.net_worth !== '' && (
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Net Worth:</span>
                    <span className="font-semibold text-white">{formatINR(formData.net_worth)}</span>
                  </div>
                )}
                {formData.emergency_fund_months && (
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Emergency Fund:</span>
                    <span className="font-semibold text-white">{formData.emergency_fund_months}</span>
                  </div>
                )}
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
                  const label = g.goal_type === 'custom' ? (g.custom_name || 'Custom Goal') : (GOAL_TYPE_OPTIONS.find((o) => o.value === g.goal_type)?.label || g.goal_type)
                  return (
                    <div
                      key={g.id || idx}
                      className="flex items-center justify-between py-2 border-b border-slate-800/60 last:border-0"
                    >
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded bg-slate-800 text-[10px] font-bold text-white border border-slate-700">
                          #{g.priority || idx + 1}
                        </span>
                        <span className="text-white font-medium capitalize">
                          {label}
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
          </div>

          {/* Review Stepper Navigation */}
          <div className="pt-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 px-5 py-2.5 text-xs font-semibold transition cursor-pointer"
            >
              &larr; Back to Risk Profile
            </button>

            <button
              type="button"
              onClick={handleFinalSubmit}
              className="rounded-xl bg-emerald-600 hover:bg-emerald-500 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition cursor-pointer"
            >
              Generate Financial Strategies &rarr;
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
