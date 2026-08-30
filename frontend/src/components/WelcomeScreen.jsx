import { useState } from 'react'

export default function WelcomeScreen({ onNewUser, onExistingUser, onEnterDemoMode }) {
  const [showSignInModal, setShowSignInModal] = useState(false)
  const [customerNameInput, setCustomerNameInput] = useState('')
  const [customerIdInput, setCustomerIdInput] = useState('')
  const [passwordInput, setPasswordInput] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showForgotMessage, setShowForgotMessage] = useState(false)
  const [signInError, setSignInError] = useState(null)

  const handleSignInSubmit = (e) => {
    e.preventDefault()
    if (!customerIdInput.trim()) {
      setSignInError('Please enter a Customer ID to continue.')
      return
    }
    setSignInError(null)
    setShowSignInModal(false)
    // Only the id is sent. The backend owns the name, so the typed name is not
    // passed on: if it were, the sign-in screen and the plan would disagree.
    onExistingUser(customerIdInput.trim())
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

        {/* Primary Action Buttons: New User vs Existing User */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 w-full max-w-md">
          {/* New User / Get Started */}
          <button
            type="button"
            onClick={onNewUser}
            className="w-full sm:w-1/2 py-3.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-sm font-bold text-white shadow-lg shadow-indigo-600/30 transition duration-200 flex items-center justify-center gap-2 cursor-pointer group"
          >
            <span>Get Started</span>
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

          {/* Existing User / Sign In */}
          <button
            type="button"
            onClick={() => setShowSignInModal(true)}
            className="w-full sm:w-1/2 py-3.5 px-6 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-sm font-semibold text-slate-200 border border-slate-800 hover:border-slate-700 transition duration-200 cursor-pointer"
          >
            Sign In
          </button>
        </div>

        {/* Distinct Development / Demo Mode Section (Visually & Semantically Separated) */}
        <div className="mt-12 w-full max-w-xl rounded-2xl border border-slate-800/80 bg-[#090e1a]/80 p-4 sm:p-5 text-left backdrop-blur-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-400 border border-amber-500/20">
                  Demo / Presentation
                </span>
                <span className="text-xs font-semibold text-slate-300">
                  Hackathon Evaluation Access
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Explore the engine with pre-computed reference data (<strong className="text-slate-300">DEMO MODE &middot; C001</strong>).
              </p>
            </div>

            <button
              type="button"
              onClick={onEnterDemoMode}
              className="shrink-0 rounded-xl bg-slate-800 hover:bg-slate-750 text-amber-300 hover:text-amber-200 border border-amber-500/30 px-3.5 py-2 text-xs font-semibold transition cursor-pointer"
            >
              Enter Demo Mode &rarr;
            </button>
          </div>
        </div>
      </div>

      {/* Sign In Modal (Authentication-Ready UI for Existing Customers) */}
      {showSignInModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm animate-fadeIn"
          onClick={() => {
            setShowSignInModal(false)
            setSignInError(null)
            setShowForgotMessage(false)
          }}
        >
          <div
            className="w-full max-w-md rounded-2xl border border-slate-800 bg-[#0d1322] p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Sign In to Your Workspace</h3>
                <p className="text-xs text-slate-400 mt-0.5">Enter your account credentials to resume financial planning</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowSignInModal(false)
                  setSignInError(null)
                  setShowForgotMessage(false)
                }}
                className="rounded-lg p-1 text-slate-400 hover:text-white hover:bg-slate-800/80 text-sm transition cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Sign-In Form */}
            <form onSubmit={handleSignInSubmit} className="space-y-3.5 text-xs">
              {/* Customer Name */}
              <div>
                <label htmlFor="customer-name" className="block font-semibold text-slate-300 mb-1">
                  Customer Name
                </label>
                <input
                  id="customer-name"
                  type="text"
                  value={customerNameInput}
                  onChange={(e) => setCustomerNameInput(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

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
                  placeholder="Enter customer ID (e.g. C001, C002)"
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 font-mono"
                  required
                />
              </div>

              {/* Password with Eye Toggle */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label htmlFor="customer-password" className="font-semibold text-slate-300">
                    Password
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
                  Password reset is managed through your wealth advisor or organization administrator in this development environment.
                </div>
              )}

              {/* Validation Error */}
              {signInError && (
                <p className="text-xs text-rose-400 font-medium">{signInError}</p>
              )}

              {/* Notice regarding backend auth readiness */}
              <div className="rounded-xl bg-slate-950/60 p-3 border border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
                <span className="font-semibold text-slate-300">Authentication Ready: </span>
                Production credential validation will connect to the backend authentication service. Entering a customer ID loads that profile&apos;s workspace.
              </div>

              {/* Form Action Buttons */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowSignInModal(false)
                    setSignInError(null)
                    setShowForgotMessage(false)
                  }}
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

            {/* Separator to Demo Mode */}
            <div className="relative flex items-center justify-center my-2">
              <div className="border-t border-slate-800 w-full" />
              <span className="bg-[#0d1322] px-2 text-[10px] uppercase font-bold text-slate-500">
                or
              </span>
            </div>

            {/* Quick Demo Access Inside Modal */}
            <div className="rounded-xl bg-amber-500/5 p-3 border border-amber-500/20 flex items-center justify-between gap-3 text-xs">
              <div>
                <p className="font-bold text-amber-300 text-xs">Demo / Presentation</p>
                <p className="text-[11px] text-slate-400">Load Persona C001 mock analysis</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowSignInModal(false)
                  onEnterDemoMode()
                }}
                className="rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 px-3 py-1.5 text-xs font-semibold transition cursor-pointer"
              >
                Enter Demo Mode
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
