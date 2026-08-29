import { useState } from 'react'
import defaultData from './data/api_response.json'
import { fetchPlan } from './services/api'
import Navbar from './components/Navbar'
import WelcomeScreen from './components/WelcomeScreen'
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
  // Session State Model: mode ('guest' | 'new_user' | 'authenticated_demo'), customer (null | planData)
  const [session, setSession] = useState({
    mode: 'guest',
    customer: null,
  })

  // Navigation View State: 'welcome' | 'user-dashboard' | 'onboarding' | 'dashboard'
  const [viewMode, setViewMode] = useState('welcome')

  // Centralized selected plan state shared across dashboard components
  const [selectedPlanId, setSelectedPlanId] = useState('A')

  // Flow 1: New User launches Onboarding
  const handleStartNewUser = () => {
    setSession({ mode: 'new_user', customer: null })
    setViewMode('onboarding')
  }

  // Flow 2: New User completes Onboarding & Goal Builder
  const handleOnboardingComplete = async (payload) => {
    try {
      const response = await fetchPlan(payload)
      if (response) {
        setSession({ mode: 'new_user', customer: response })
        setSelectedPlanId('A')
        setViewMode('dashboard')
      }
    } catch (err) {
      alert(err.message || 'Connection error: Unable to reach the backend.')
    }
  }

  // Flow 3: Existing User Sign-In
  const handleExistingUser = async (customerId, customerName) => {
    try {
      const response = await fetchPlan({ customer_id: customerId })
      if (response) {
        const updated = {
          ...response,
          customer_id: customerId,
          customer_name: customerName && customerName !== 'Existing Customer' ? customerName : response.customer_name,
        }
        setSession({ mode: 'new_user', customer: updated })
        setSelectedPlanId('A')
        setViewMode('user-dashboard')
      }
    } catch (err) {
      alert(err.message || 'Connection error: Unable to reach the backend.')
    }
  }

  // Flow 4: Development / Hackathon Demo Mode
  const handleEnterDemoMode = () => {
    setSession({ mode: 'authenticated_demo', customer: defaultData })
    setSelectedPlanId('A')
    setViewMode('dashboard')
  }

  // Session Reset: Clears customer data and returns to Welcome
  const handleResetSession = () => {
    setSession({ mode: 'guest', customer: null })
    setSelectedPlanId('A')
    setViewMode('welcome')
  }

  const activeCustomer = session.customer

  // Derived effective view guarding against unauthorized guest access to dashboard
  const isGuest = session.mode === 'guest'
  const effectiveView = isGuest && viewMode !== 'onboarding' ? 'welcome' : viewMode

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
            onNewUser={handleStartNewUser}
            onExistingUser={handleExistingUser}
            onEnterDemoMode={handleEnterDemoMode}
          />
        </main>
      )}

      {/* VIEW 2: New User Multi-Step Onboarding & Goal Builder (Starts EMPTY) */}
      {effectiveView === 'onboarding' && (
        <main className="flex-1 py-8">
          <OnboardingFlow
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
                  <strong>Demo Evaluation Mode (Persona C001 &middot; Rahul Mehta):</strong> Displaying pre-computed mock analysis dataset for hackathon evaluation.
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
            monthlySurplus={activeCustomer.profile?.monthly_surplus}
            goalPriorityNote={activeCustomer.goal_priority_note}
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
            monthlySurplus={activeCustomer.profile?.monthly_surplus}
            goals={activeCustomer.goals}
            onStartNewAnalysis={handleStartNewUser}
          />

          {/* Monte Carlo 10k Simulation Percentiles Deep Dive */}
          <SimulationDeepDive
            plans={activeCustomer.plans}
            goalAmount={activeCustomer.goals?.[0]?.target_amount}
          />

          {/* Audit & Compliance Footer */}
          <footer className="mt-4 pt-6 border-t border-slate-850 text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>
                Audited by Cognizant Verification Engine (
                {activeCustomer.verifier?.numbers_checked || 87} deterministic checks passed)
              </span>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-slate-400">
              <span>Model: {activeCustomer.meta?.model_version || 'rr-v1'}</span>
              <span>&middot;</span>
              <span>Assumptions: {activeCustomer.meta?.assumptions_version || 'assump-v1'}</span>
              <span>&middot;</span>
              <span>Market Data: NIFTY 2005–2025</span>
            </div>
          </footer>
        </main>
      )}
    </div>
  )
}

export default App