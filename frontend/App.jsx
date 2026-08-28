import React, { useState } from 'react';
import RiskInsight from './RiskInsight.jsx';
import SimilarProfiles from './SimilarProfiles.jsx';

// Import raw mock data
import mockApiResponseMismatch from '../mocks/api_response.json';
import mockApiResponseAligned from '../mocks/api_response_aligned.json';
import mockPeerCohort from '../mocks/peer_cohort_mock.json';

export default function App() {
  const [activeScreen, setActiveScreen] = useState('3.6'); // '3.6' | '3.7'
  const [selectedPersona, setSelectedPersona] = useState('C001'); // 'C001' | 'C002' | 'NULLS'
  const [simulatedState, setSimulatedState] = useState('success'); // 'success' | 'loading' | 'error' | 'empty'
  const [mismatchOverride, setMismatchOverride] = useState(null);

  // Select appropriate mock dataset
  let currentApiData = null;
  if (simulatedState === 'success') {
    if (selectedPersona === 'C001') {
      currentApiData = JSON.parse(JSON.stringify(mockApiResponseMismatch));
    } else if (selectedPersona === 'C002') {
      currentApiData = JSON.parse(JSON.stringify(mockApiResponseAligned));
    } else if (selectedPersona === 'NULLS') {
      currentApiData = {
        customer_name: "Null Field Test Persona",
        profile: {
          net_worth: null,
          monthly_income: null,
          monthly_expense: null,
          monthly_surplus: null,
          emergency_fund_months: null,
        },
        risk: {
          stated: null,
          revealed: null,
          confidence: null,
          mismatch: true,
          risk_capacity: null,
          features_used: {
            panic_sell_count: null,
            avg_days_to_exit_after_drop: null,
            expense_volatility: null,
            emergency_fund_months: null,
            equity_allocation_pct: null,
            budget_overshoot_rate: null,
          },
          evidence: [
            "Null/Edge case test: all missing fields must render strictly as '—' rather than 0 or empty.",
          ],
          model_version: "rr-null-test",
        },
        peer_cohort: null,
      };
    }

    if (currentApiData && mismatchOverride !== null && currentApiData.risk) {
      currentApiData.risk.mismatch = mismatchOverride;
    }
  }

  const isLoading = simulatedState === 'loading';
  const isError = simulatedState === 'error' ? "Simulated API gateway timeout (504)" : null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-slate-950">
      
      {/* Top Application Bar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
          
          {/* Logo & Hackathon Team Badge */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center font-black text-slate-950 text-lg shadow-lg shadow-emerald-500/20">
              ₹
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base text-white tracking-tight">FinancePlanner</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Varada's Screens
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Team Hackathon Demo · Branch: feature/features</p>
            </div>
          </div>

          {/* Screen Navigation Tabs */}
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-1 shadow-inner">
            <button
              onClick={() => setActiveScreen('3.6')}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                activeScreen === '3.6'
                  ? 'bg-emerald-500 text-slate-950 shadow-md font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <span>Screen 3.6: Risk Insight</span>
              <span className={`text-[9px] px-1 py-0.2 rounded font-mono ${activeScreen === '3.6' ? 'bg-slate-950/20 text-slate-950' : 'bg-slate-800 text-slate-400'}`}>
                STAR
              </span>
            </button>
            <button
              onClick={() => setActiveScreen('3.7')}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                activeScreen === '3.7'
                  ? 'bg-emerald-500 text-slate-950 shadow-md font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <span>Screen 3.7: Similar Profiles</span>
              <span className={`text-[9px] px-1 py-0.2 rounded font-mono ${activeScreen === '3.7' ? 'bg-slate-950/20 text-slate-950' : 'bg-slate-800 text-slate-400'}`}>
                COHORT
              </span>
            </button>
          </div>

          {/* Persona & State Demo Selectors */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Persona Selector */}
            <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Persona:</span>
              <select
                value={selectedPersona}
                onChange={(e) => {
                  setSelectedPersona(e.target.value);
                  setMismatchOverride(null);
                  if (simulatedState === 'empty') setSimulatedState('success');
                }}
                className="bg-transparent text-xs text-slate-200 font-medium focus:outline-none cursor-pointer"
              >
                <option value="C001" className="bg-slate-900 text-slate-200">C001 (Rahul - Mismatch)</option>
                <option value="C002" className="bg-slate-900 text-slate-200">C002 (Priya - Aligned)</option>
                <option value="NULLS" className="bg-slate-900 text-slate-200">Nulls / Missing Fields Test</option>
              </select>
            </div>

            {/* State Simulator */}
            <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">State:</span>
              <select
                value={simulatedState}
                onChange={(e) => setSimulatedState(e.target.value)}
                className="bg-transparent text-xs text-slate-200 font-medium focus:outline-none cursor-pointer"
              >
                <option value="success" className="bg-slate-900 text-slate-200">Normal (Success)</option>
                <option value="loading" className="bg-slate-900 text-slate-200">Loading Skeleton</option>
                <option value="error" className="bg-slate-900 text-slate-200">Error State</option>
                <option value="empty" className="bg-slate-900 text-slate-200">Empty State</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 py-6 px-3 sm:px-6">
        {activeScreen === '3.6' ? (
          <RiskInsight
            apiData={currentApiData}
            isLoading={isLoading}
            error={isError}
            onNavigateToPlans={() => alert("Navigating to Screen 4 (Plan Recommendations)...")}
            onNavigateToCohort={() => setActiveScreen('3.7')}
            onToggleMismatchOverride={(overrideVal) => setMismatchOverride(overrideVal)}
          />
        ) : (
          <SimilarProfiles
            cohortData={mockPeerCohort}
            apiData={currentApiData}
            isLoading={isLoading}
            error={isError}
            onNavigateToRiskInsight={() => setActiveScreen('3.6')}
            onNavigateToPlans={() => alert("Navigating to Screen 4 (Plan Recommendations)...")}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-400">
        Finance-Planner Hackathon UI · Single-file React Components · Pure Display Formatting (Zero Calculations in Frontend)
      </footer>
    </div>
  );
}
