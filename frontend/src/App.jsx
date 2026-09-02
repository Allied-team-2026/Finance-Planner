import { useState } from 'react'
import { fetchPlan } from './services/api'
import Navbar from './components/Navbar'
import WelcomeScreen from './components/WelcomeScreen'
import PipelineLoading from './components/PipelineLoading'
import UserDashboard from './components/UserDashboard'
import OnboardingFlow from './components/OnboardingFlow'
import CustomerSnapshot from './components/CustomerSnapshot'
import FinancialJourney3D from './components/FinancialJourney3D'
import RiskMismatchAlert from './components/RiskMismatchAlert'
import PlanComparison from './components/PlanComparison'
import WhatIfAnalysis from './components/WhatIfAnalysis'
import ChallengePlan from './components/ChallengePlan'
import SelectedPlanSummary from './components/SelectedPlanSummary'
import SimulationDeepDive from './components/SimulationDeepDive'
import VerificationBanner from './components/VerificationBanner'

function App() {
  // Session State Model: mode ('guest' | 'authenticated'), customer (null | planData), customerId (null | string)
  const [session, setSession] = useState({
    mode: 'guest',
    customer: null,
    customerId: null,
  })

  // Navigation View State: 'welcome' | 'orchestrating' | 'user-dashboard' | 'onboarding' | 'dashboard'
  const [viewMode, setViewMode] = useState('welcome')

  // Centralized selected plan state shared across dashboard components
  const [selectedPlanId, setSelectedPlanId] = useState('A')

  // Flow 1: Sign In Success -> Launch WealthIQ Orchestration Pipeline
  const handleSignInSuccess = (customerId) => {
    setSession({ mode: 'authenticated', customer: null, customerId })
    setViewMode('orchestrating')
  }

  // Flow 1b: Start new analysis from dashboard or flow
  const handleStartNewUser = (customerId) => {
    const activeId = customerId || session.customerId || 'C001'
    setSession({ mode: 'authenticated', customer: null, customerId: activeId })
    setViewMode('orchestrating')
  }

  // Flow 1c: Pipeline completes verification -> transition automatically to Customer Profile Review
  const handlePipelineComplete = (planData) => {
    setSession({
      mode: 'authenticated',
      customer: planData,
      customerId: planData.customer_id || session.customerId,
    })
    setSelectedPlanId('A')
    setViewMode('onboarding')
  }

  // Flow 2: User completes Profile Review & Goal Confirmation -> Launch Planner Dashboard
  const handleOnboardingComplete = async (payload) => {
    if (session.customer && session.customer.customer_id === (payload?.customer_id || session.customerId)) {
      setSelectedPlanId('A')
      setViewMode('dashboard')
      return
    }

    try {
      const response = await fetchPlan(payload)
      if (response) {
        setSession({
          mode: 'authenticated',
          customer: response,
          customerId: payload.customer_id || session.customerId,
        })
        setSelectedPlanId('A')
        setViewMode('dashboard')
      }
    } catch (err) {
      alert(err.message || 'Connection error: Unable to reach the backend.')
    }
  }

  // Session Reset: Clears customer data and returns to Welcome
  const handleResetSession = () => {
    setSession({ mode: 'guest', customer: null, customerId: null })
    setSelectedPlanId('A')
    setViewMode('welcome')
  }

  const activeCustomer = session.customer

  // Derived effective view guarding against unauthorized guest access to dashboard
  const isGuest = session.mode === 'guest'
  const effectiveView = isGuest && viewMode !== 'onboarding' && viewMode !== 'orchestrating' ? 'welcome' : viewMode

  return (
    <div className="min-h-screen bg-[#080C14] text-slate-100 flex flex-col antialiased selection:bg-indigo-500 selection:text-white">
      {/* Top Fintech Navigation Bar */}
      <Navbar
        session={session}
        onResetSession={handleResetSession}
        onNavigateWorkspace={() => setViewMode('user-dashboard')}
        viewMode={effectiveView}
      />

      {/* VIEW 1: Landing / Welcome Screen (Default state for Guest) */}
      {effectiveView === 'welcome' && (
        <main className="flex-1">
          <WelcomeScreen
            onSignInSuccess={handleSignInSuccess}
            onNewUser={handleSignInSuccess}
          />
        </main>
      )}

      {/* VIEW 2: WealthIQ Orchestration / Engine Pipeline Visualization */}
      {effectiveView === 'orchestrating' && (
        <main className="flex-1 overflow-hidden">
          <PipelineLoading
            customerId={session.customerId || 'C001'}
            onComplete={handlePipelineComplete}
            onCancel={handleResetSession}
          />
        </main>
      )}

      {/* VIEW 3: Customer Profile & Parameter Review */}
      {effectiveView === 'onboarding' && (
        <main className="flex-1 py-8">
          <OnboardingFlow
            key={session.customerId || 'default'}
            customerId={session.customerId || 'C001'}
            initialCustomerId={session.customerId || 'C001'}
            preloadedData={session.customer}
            onComplete={handleOnboardingComplete}
            onCancel={handleResetSession}
          />
        </main>
      )}

      {/* VIEW 3: Existing User Workspace Dashboard (Protected) */}
      {effectiveView === 'user-dashboard' && activeCustomer && (
        <main className="flex-1">
          <UserDashboard
            customerName={activeCustomer.customer_name}
            customerId={activeCustomer.customer_id}
            profile={activeCustomer.profile}
            goals={activeCustomer.goals}
            plans={activeCustomer.plans}
            selectedPlanId={selectedPlanId}
            generatedAt={activeCustomer.generated_at}
            nSimulations={activeCustomer.meta?.n_simulations}
            onViewLatestAnalysis={() => setViewMode('dashboard')}
            onStartNewAnalysis={handleStartNewUser}
          />
        </main>
      )}

      {/* VIEW 4: In-depth Strategy Analysis & Decision Dashboard (Protected) */}
      {effectiveView === 'dashboard' && activeCustomer && (
        <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8 animate-fadeIn">
          {/* Demo Customer Banner (Only visible when Demo Mode is explicitly active) */}
          {session.mode === 'authenticated_demo' && (
            <div className="rounded-xl bg-amber-500/10 p-3.5 border border-amber-500/25 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-200">
              <div className="flex items-center gap-2.5">
                <span className="flex h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
                <span>
                  <strong>
                    Demo Evaluation Mode ({activeCustomer.customer_id} &middot; {activeCustomer.customer_name}):
                  </strong> Displaying pre-computed mock analysis dataset for hackathon evaluation.
                </span>
              </div>
              <button
                type="button"
                onClick={handleResetSession}
                className="self-start sm:self-auto rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 px-3 py-1 text-[11px] font-semibold border border-amber-500/30 transition cursor-pointer"
              >
                Exit Demo
              </button>
            </div>
          )}

          {/* Verification Banner */}
          <VerificationBanner verifier={activeCustomer.verifier} />

          {/* Customer Context & Financial Health Snapshot */}
          <CustomerSnapshot
            customerName={activeCustomer.customer_name}
            context={activeCustomer.context}
            profile={activeCustomer.profile}
            goals={activeCustomer.goals}
            peerCohort={activeCustomer.peer_cohort}
          />

          {/* 3D Financial Journey Centerpiece */}
          <FinancialJourney3D
            profile={activeCustomer.profile}
            goals={activeCustomer.goals}
            plans={activeCustomer.plans}
            selectedPlanId={selectedPlanId}
            onSelectPlan={setSelectedPlanId}
          />

          {/* Behavioral Risk Mismatch Intelligence Banner */}
          <RiskMismatchAlert
            risk={activeCustomer.risk}
            mismatchNote={activeCustomer.mismatch_note}
            profile={activeCustomer.profile}
          />

          {/* 3-Plan Strategic Comparison Section */}
          <PlanComparison
            plans={activeCustomer.plans}
            goalPriorityNote={activeCustomer.goal_priority_note}
            nSimulations={activeCustomer.meta?.n_simulations}
            selectedPlanId={selectedPlanId}
            onSelectPlan={setSelectedPlanId}
          />

          {/* Real-time What-If Scenario Sensitivity Testing */}
          <WhatIfAnalysis
            plans={activeCustomer.plans}
            selectedPlanId={selectedPlanId}
            monthlySurplus={activeCustomer.profile?.monthly_surplus}
            customerId={activeCustomer.customer_id}
          />

          {/* Pre-Commitment Challenge Your Pick Workflow */}
          <ChallengePlan
            plans={activeCustomer.plans}
            selectedPlanId={selectedPlanId}
            onSelectPlan={setSelectedPlanId}
            customerId={activeCustomer.customer_id}
            initialChallenge={activeCustomer.challenge}
          />

          {/* Final Selected Plan Summary & Decision Verification */}
          <SelectedPlanSummary
            plans={activeCustomer.plans}
            selectedPlanId={selectedPlanId}
            goals={activeCustomer.goals}
            onStartNewAnalysis={handleStartNewUser}
          />

          {/* Monte Carlo 10k Simulation Percentiles Deep Dive */}
          <SimulationDeepDive
            plans={activeCustomer.plans}
            goalAmount={activeCustomer.goals?.[0]?.target_amount}
            nSimulations={activeCustomer.meta?.n_simulations}
          />

          {/* Audit & Compliance Footer */}
          <footer className="mt-4 pt-6 border-t border-slate-850 text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${
                activeCustomer.verifier?.status === 'fail' ? 'bg-rose-500' : 'bg-emerald-500'
              }`} />
              <span>
                {activeCustomer.verifier == null
                  ? 'Verification not reported'
                  : `Cognizant Verification Engine: ${activeCustomer.verifier.numbers_checked} numbers checked, ${
                      activeCustomer.verifier.status === 'fail' ? 'verification failed' : 'all matched'
                    }`}
              </span>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-slate-400">
              <span>Model: {activeCustomer.meta?.model_version ?? '—'}</span>
              <span>&middot;</span>
              <span>Assumptions: {activeCustomer.meta?.assumptions_version ?? '—'}</span>
              <span>&middot;</span>
              <span>Returns: {activeCustomer.meta?.returns_data_source ?? '—'}</span>
            </div>
          </footer>
        </main>
      )}
    </div>
  )
}

export default App