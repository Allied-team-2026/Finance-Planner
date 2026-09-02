import { useState } from 'react'
import { DEMO_CREDENTIALS, validateCredentials } from '../data/demoCredentials'

export default function WelcomeScreen({ onSignInSuccess, onNewUser }) {
  const [showSignInModal, setShowSignInModal] = useState(false)
  const [customerIdInput, setCustomerIdInput] = useState('')
  const [passwordInput, setPasswordInput] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showForgotMessage, setShowForgotMessage] = useState(false)
  const [signInError, setSignInError] = useState(null)

  const handleSignInSubmit = (e) => {
    e.preventDefault()
    const result = validateCredentials(customerIdInput, passwordInput)
    if (!result.isValid) {
      setSignInError(result.error)
      return
    }
    setSignInError(null)
    setShowSignInModal(false)
    const authedId = result.customer.customerId
    if (onSignInSuccess) {
      onSignInSuccess(authedId)
    } else if (onNewUser) {
      onNewUser(authedId)
    }
  }

  const handleQuickFill = (id) => {
    setCustomerIdInput(id)
    setPasswordInput('demoPassword123')
    setSignInError(null)
  }

  const handleCloseModal = () => {
    setShowSignInModal(false)
    setSignInError(null)
    setShowForgotMessage(false)
  }

  return (
    <div className="relative min-h-[85vh] flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
      {/* Background Subtle Accent Elements */}
      <div className="absolute top-1/4 -left-20 h-72 w-72 rounded-full bg-indigo-600/10 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-20 h-72 w-72 rounded-full bg-cyan-600/10 blur-3xl pointer-events-none" />

      {/* Main Hero Card Container */}
      <div className="relative z-10 max-w-3xl w-full flex flex-col items-center text-center">
        {/* Trust & Intelligence Badge */}
        <div className="inline-flex items-center gap-2 rounded-full bg-indigo-500/10 px-3.5 py-1.5 border border-indigo-500/20 text-indigo-400 text-xs font-semibold mb-6">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Cognizant WealthIQ Decision Engine</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white leading-tight">
          Plan your money <br />
          <span className="bg-gradient-to-r from-cyan-400 via-indigo-300 to-indigo-500 bg-clip-text text-transparent">
            around your life.
          </span>
        </h1>

        {/* Supporting Subtitle */}
        <p className="mt-5 max-w-2xl text-base sm:text-lg text-slate-300 leading-relaxed font-normal">
          Build your financial profile, compare personalized strategies, and test them before you commit.
        </p>

        {/* Core Value Pillars Grid */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-3.5 w-full max-w-2xl text-left">
          <div className="rounded-xl bg-[#0d1322]/80 p-3.5 border border-slate-800 backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs font-bold text-white mb-1">
              <span className="text-cyan-400">01</span>
              <span>Contextual Profiling</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Accounts for your surplus, dependents, risk capacity, and time horizons.
            </p>
          </div>

          <div className="rounded-xl bg-[#0d1322]/80 p-3.5 border border-slate-800 backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs font-bold text-white mb-1">
              <span className="text-indigo-400">02</span>
              <span>10k Monte Carlo Tests</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Evaluates strategies through market simulations and adverse stress combinations.
            </p>
          </div>

          <div className="rounded-xl bg-[#0d1322]/80 p-3.5 border border-slate-800 backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs font-bold text-white mb-1">
              <span className="text-emerald-400">03</span>
              <span>Challenger AI</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Pre-commitment audits test your plan against past behavioural drop points.
            </p>
          </div>
        </div>

        {/* Primary Action Button: Sign In (renamed from Get Started) */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 w-full max-w-md">
          <button
            type="button"
            onClick={() => {
              setSignInError(null)
              setShowSignInModal(true)
            }}
            className="w-full sm:w-1/2 py-3.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-sm font-bold text-white shadow-lg shadow-indigo-600/30 transition duration-200 flex items-center justify-center gap-2 cursor-pointer group"
          >
            <span>Sign In</span>
            <svg
              className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </div>

      {/* Sign In Modal (Clean Professional Fintech-style) */}
      {showSignInModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm animate-fadeIn"
          onClick={handleCloseModal}
        >
          <div
            className="w-full max-w-md rounded-2xl border border-slate-800 bg-[#0d1322] p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Sign In to Your Workspace</h3>
                <p className="text-xs text-slate-400 mt-0.5">Enter your account credentials to access financial planning</p>
              </div>
              <button
                type="button"
                onClick={handleCloseModal}
                className="rounded-lg p-1 text-slate-400 hover:text-white hover:bg-slate-800/80 text-sm transition cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Demo Accounts Quick-Select Badge */}
            <div className="rounded-xl bg-slate-950/70 border border-slate-800/80 p-3 text-xs space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span className="font-semibold text-slate-300">Demo Accounts Available:</span>
                <span className="font-mono text-slate-400">Password: <code className="text-indigo-400 font-bold">demoPassword123</code></span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {Object.values(DEMO_CREDENTIALS).map((item) => (
                  <button
                    key={item.customerId}
                    type="button"
                    onClick={() => handleQuickFill(item.customerId)}
                    className="p-1.5 rounded-lg border border-slate-800 hover:border-indigo-500/50 bg-slate-900/80 hover:bg-indigo-950/30 text-left transition cursor-pointer"
                  >
                    <div className="font-mono font-bold text-[11px] text-indigo-400">{item.customerId}</div>
                    <div className="text-[10px] text-slate-300 truncate">{item.customerName}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Sign-In Form */}
            <form onSubmit={handleSignInSubmit} className="space-y-3.5 text-xs">
              {/* Customer ID */}
              <div>
                <label htmlFor="customer-id" className="block font-semibold text-slate-300 mb-1">
                  Customer ID <span className="text-rose-400">*</span>
                </label>
                <input
                  id="customer-id"
                  type="text"
                  value={customerIdInput}
                  onChange={(e) => setCustomerIdInput(e.target.value)}
                  placeholder="Enter customer ID (e.g. C001, C002, C003)"
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 font-mono uppercase"
                  required
                />
              </div>

              {/* Password with Eye Toggle */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label htmlFor="customer-password" className="font-semibold text-slate-300">
                    Password <span className="text-rose-400">*</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowForgotMessage(!showForgotMessage)}
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 transition cursor-pointer"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <input
                    id="customer-password"
                    type={showPassword ? 'text' : 'password'}
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    placeholder="Enter password"
                    className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 pr-10 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 font-mono"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition cursor-pointer"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </svg>
                    ) : (
                      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Forgot Password Message */}
              {showForgotMessage && (
                <div className="rounded-xl bg-slate-950/80 p-2.5 border border-slate-800 text-[11px] text-slate-300">
                  Demo password for all 3 demo accounts (C001, C002, C003) is <strong className="text-indigo-400 font-mono">demoPassword123</strong>.
                </div>
              )}

              {/* Validation Error Banner */}
              {signInError && (
                <div className="rounded-xl bg-rose-500/10 p-3 border border-rose-500/25 flex items-start gap-2.5 text-xs text-rose-300">
                  <svg className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>{signInError}</span>
                </div>
              )}

              {/* Form Action Buttons */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="w-1/2 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-300 border border-slate-800 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 cursor-pointer"
                >
                  Sign In &rarr;
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
