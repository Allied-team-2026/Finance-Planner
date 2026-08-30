import { useState, useEffect, useMemo, useRef, Component } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Html, Float } from '@react-three/drei'
import * as THREE from 'three'

function formatINR(amount) {
  if (amount == null || isNaN(amount)) return '—'
  return `₹${Math.round(Number(amount)).toLocaleString('en-IN')}`
}

// Error Boundary for WebGL Rendering
class WebGLErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.warn('[FinancialJourney3D] WebGL Canvas error, falling back to 2D visualization:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}

// Check WebGL context availability safely
function checkWebGLSupport() {
  if (typeof window === 'undefined') return false
  try {
    const canvas = document.createElement('canvas')
    return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')))
  } catch {
    return false
  }
}

// 3D Origin Node representing "NOW" (Current Financial Baseline)
function OriginNode({ monthlySurplus }) {
  const meshRef = useRef()

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.4
    }
  })

  return (
    <group position={[-4.2, -0.6, 0]}>
      <mesh ref={meshRef}>
        <octahedronGeometry args={[0.35, 0]} />
        <meshStandardMaterial
          color="#38bdf8"
          roughness={0.2}
          metalness={0.8}
          wireframe={false}
        />
      </mesh>

      {/* Orbiting halo ring */}
      <mesh rotation={[Math.PI / 2.5, 0, 0]}>
        <torusGeometry args={[0.55, 0.02, 16, 32]} />
        <meshBasicMaterial color="#38bdf8" transparent opacity={0.5} />
      </mesh>

      {/* Origin Label */}
      <Html position={[0, -0.85, 0]} center distanceFactor={10}>
        <div className="pointer-events-none select-none rounded-lg border border-cyan-500/30 bg-[#080d18]/90 px-2.5 py-1 text-center shadow-lg backdrop-blur-md whitespace-nowrap">
          <p className="text-[9px] font-bold uppercase tracking-wider text-cyan-400">NOW</p>
          <p className="text-[11px] font-extrabold text-white">
            {formatINR(monthlySurplus)} <span className="text-[9px] text-slate-400 font-normal">/ mo surplus</span>
          </p>
        </div>
      </Html>
    </group>
  )
}

// 3D Trajectory Path for Each Strategy
function PlanPathway({ isSelected, curve, color }) {
  const points = useMemo(() => curve.getPoints(50), [curve])
  const lineGeometry = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points])

  return (
    <group>
      {/* Underlying trajectory curve */}
      <line geometry={lineGeometry}>
        <lineBasicMaterial
          color={color}
          linewidth={isSelected ? 3 : 1}
          transparent
          opacity={isSelected ? 0.95 : 0.22}
        />
      </line>

      {/* Tube mesh for active/selected path to give it tactile depth */}
      {isSelected && (
        <mesh>
          <tubeGeometry args={[curve, 40, 0.045, 8, false]} />
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={0.35}
            roughness={0.3}
            metalness={0.7}
          />
        </mesh>
      )}
    </group>
  )
}

// 3D Goal Milestone Pin along the Strategy Path
function GoalMilestone({ goal, position, isPrimary, isSelected }) {
  const pinRef = useRef()

  useFrame((state) => {
    if (pinRef.current && isSelected) {
      pinRef.current.position.y = position[1] + Math.sin(state.clock.getElapsedTime() * 2 + position[0]) * 0.06
    }
  })

  return (
    <group position={position}>
      {/* Vertical light beacon line */}
      <line>
        <bufferGeometry
          attach="geometry"
          onUpdate={(self) => {
            self.setFromPoints([new THREE.Vector3(0, -1.2, 0), new THREE.Vector3(0, 0.4, 0)])
          }}
        />
        <lineBasicMaterial color={isPrimary ? '#10b981' : '#6366f1'} transparent opacity={0.35} />
      </line>

      {/* Milestone Node */}
      <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.3}>
        <mesh ref={pinRef}>
          <sphereGeometry args={[isPrimary ? 0.22 : 0.18, 24, 24]} />
          <meshStandardMaterial
            color={isPrimary ? '#10b981' : '#818cf8'}
            emissive={isPrimary ? '#059669' : '#4f46e5'}
            emissiveIntensity={0.4}
            roughness={0.2}
            metalness={0.6}
          />
        </mesh>
      </Float>

      {/* Floating Goal Milestone HTML Badge */}
      <Html position={[0, 0.7, 0]} center distanceFactor={9}>
        <div className="pointer-events-none select-none rounded-xl border border-slate-800 bg-[#0a101d]/95 p-2 text-center shadow-xl backdrop-blur-md whitespace-nowrap">
          <div className="flex items-center justify-center gap-1.5 mb-0.5">
            <span className={`h-1.5 w-1.5 rounded-full ${isPrimary ? 'bg-emerald-400 animate-pulse' : 'bg-indigo-400'}`} />
            <span className="text-[9px] font-bold uppercase tracking-wider text-slate-300">
              {goal.displayName || goal.name?.replace(/_/g, ' ') || 'Goal'}
            </span>
          </div>
          <p className="text-xs font-extrabold text-white">
            {formatINR(goal.target_amount)}
          </p>
          <p className="text-[10px] text-slate-400">
            in {goal.years} years &middot; Priority #{goal.priority || 1}
          </p>
        </div>
      </Html>
    </group>
  )
}

// Main 3D Canvas Scene
function JourneyScene({ plans, selectedPlanId, goals, monthlySurplus, prefersReducedMotion }) {
  // Define 3 Distinct Spatial Curves for the 3 Strategic Options:
  // Plan A (Steady): Moderate ascent, highly stable, lower volatility
  // Plan B (Balanced): Balanced upward curve
  // Plan C (Growth): Steeper trajectory
  const planCurves = useMemo(() => {
    return {
      A: new THREE.CatmullRomCurve3([
        new THREE.Vector3(-4.2, -0.6, 0),
        new THREE.Vector3(-1.8, -0.2, 0.4),
        new THREE.Vector3(0.8, 0.35, 0.2),
        new THREE.Vector3(3.8, 0.85, 0),
      ]),
      B: new THREE.CatmullRomCurve3([
        new THREE.Vector3(-4.2, -0.6, 0),
        new THREE.Vector3(-1.8, 0.0, -0.3),
        new THREE.Vector3(0.8, 0.7, -0.2),
        new THREE.Vector3(3.8, 1.25, 0),
      ]),
      C: new THREE.CatmullRomCurve3([
        new THREE.Vector3(-4.2, -0.6, 0),
        new THREE.Vector3(-1.8, 0.3, -0.8),
        new THREE.Vector3(0.8, 1.15, -0.6),
        new THREE.Vector3(3.8, 1.85, 0),
      ]),
    }
  }, [])

  // Position goals dynamically along the selected plan curve
  const activeCurve = planCurves[selectedPlanId] || planCurves.A
  const goalPositions = useMemo(() => {
    if (!goals || goals.length === 0) return []
    const maxYears = Math.max(...goals.map((g) => g.years || 5), 10)

    return goals.map((g, idx) => {
      // Map years [1..maxYears] to t in [0.25..0.95] along the curve
      const rawT = (g.years || 5) / maxYears
      const t = THREE.MathUtils.clamp(0.25 + rawT * 0.7, 0.25, 0.95)
      const pt = activeCurve.getPoint(t)
      return {
        goal: g,
        position: [pt.x, pt.y, pt.z],
        isPrimary: idx === 0,
      }
    })
  }, [goals, activeCurve])

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.65} />
      <directionalLight position={[6, 8, 5]} intensity={1.1} color="#ffffff" />
      <pointLight position={[-4, 2, 2]} intensity={0.8} color="#38bdf8" />
      <pointLight position={[3, 3, 2]} intensity={0.9} color="#10b981" />

      {/* Subtle floor grid reference for depth */}
      <gridHelper
        args={[16, 16, '#1e293b', '#0f172a']}
        position={[0, -1.5, 0]}
        rotation={[0, 0, 0]}
      />

      {/* Camera Controls with clamped bounds */}
      <OrbitControls
        enableZoom={false}
        enablePan={false}
        autoRotate={!prefersReducedMotion}
        autoRotateSpeed={0.35}
        minPolarAngle={Math.PI / 3}
        maxPolarAngle={Math.PI / 2.1}
        minAzimuthAngle={-Math.PI / 8}
        maxAzimuthAngle={Math.PI / 8}
        dampingFactor={0.05}
      />

      {/* Origin "NOW" Node */}
      <OriginNode monthlySurplus={monthlySurplus} />

      {/* 3 Strategy Pathways */}
      <PlanPathway
        plan={plans?.find((p) => p.plan_id === 'A')}
        isSelected={selectedPlanId === 'A'}
        curve={planCurves.A}
        color="#38bdf8"
      />
      <PlanPathway
        plan={plans?.find((p) => p.plan_id === 'B')}
        isSelected={selectedPlanId === 'B'}
        curve={planCurves.B}
        color="#818cf8"
      />
      <PlanPathway
        plan={plans?.find((p) => p.plan_id === 'C')}
        isSelected={selectedPlanId === 'C'}
        curve={planCurves.C}
        color="#34d399"
      />

      {/* Goal Milestones along active curve */}
      {goalPositions.map((gp, idx) => (
        <GoalMilestone
          key={gp.goal.id || idx}
          goal={gp.goal}
          position={gp.position}
          isPrimary={gp.isPrimary}
          isSelected={true}
        />
      ))}
    </>
  )
}

// 2D HTML/SVG Fallback Visualization (Gracefully rendered if WebGL is unavailable)
function FallbackJourney2D({ profile = {}, goals = [], plans = [], selectedPlanId = 'A' }) {
  const activePlan = plans.find((p) => p.plan_id === selectedPlanId) || plans[0]

  return (
    <div className="relative rounded-2xl border border-slate-800 bg-[#080d18] p-6 text-slate-200">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-6">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
            Financial Journey Roadmap
          </span>
          <h4 className="text-sm font-bold text-white mt-0.5">Capital Timeline & Milestone Progression</h4>
        </div>
        <span className="rounded-lg bg-slate-900 px-2.5 py-1 text-[11px] font-mono text-slate-400 border border-slate-800">
          Strategy {activePlan?.plan_id ?? '—'} Active
        </span>
      </div>

      <div className="relative flex flex-col md:flex-row items-center justify-between gap-6 py-4">
        {/* Origin: NOW */}
        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-bold text-xs shadow-lg">
            NOW
          </div>
          <p className="mt-2 text-xs font-bold text-white">{formatINR(profile.monthly_surplus)}/mo</p>
          <p className="text-[10px] text-slate-400">Monthly Surplus</p>
        </div>

        {/* Horizontal Connecting Track */}
        <div className="flex-1 w-full md:w-auto h-1.5 bg-gradient-to-r from-cyan-500/40 via-indigo-500/40 to-emerald-500/60 rounded-full relative my-2 md:my-0">
          <div className="absolute inset-0 bg-indigo-400/20 animate-pulse rounded-full" />
        </div>

        {/* Dynamic Goals along path */}
        {goals && goals.length > 0 ? (
          goals.map((g, idx) => (
            <div key={g.id || idx} className="flex flex-col items-center text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold text-xs shadow-lg">
                #{g.priority || idx + 1}
              </div>
              <p className="mt-2 text-xs font-bold text-white capitalize truncate max-w-[130px]">
                {g.displayName || g.name?.replace(/_/g, ' ') || 'Goal'}
              </p>
              <p className="text-[11px] font-extrabold text-emerald-400">{formatINR(g.target_amount)}</p>
              <p className="text-[10px] text-slate-400">in {g.years} years</p>
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold text-xs shadow-lg">
              Goal
            </div>
            <p className="mt-2 text-xs font-bold text-white">Target Milestone</p>
            <p className="text-[10px] text-slate-400">5-Year Horizon</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Master FinancialJourney3D Component
export default function FinancialJourney3D({
  profile = {},
  goals = [],
  plans = [],
  selectedPlanId = 'A',
  onSelectPlan,
}) {
  const [isSupported] = useState(() => checkWebGLSupport())
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches
    }
    return false
  })

  // Listen to media query changes
  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
      const handler = (e) => setPrefersReducedMotion(e.matches)
      mediaQuery.addEventListener('change', handler)
      return () => mediaQuery.removeEventListener('change', handler)
    }
  }, [])

  const selectedPlan = plans.find((p) => p.plan_id === selectedPlanId) || plans[0]
  const primaryGoal = goals && goals.length > 0 ? goals[0] : null
  // Passed straight to formatINR, which shows a dash. Defaulting to 0 here would
  // print "₹0 / mo surplus" as if the engine had said so.
  const monthlySurplus = profile.monthly_surplus ?? null

  return (
    <section className="flex flex-col gap-5">
      {/* 1. Header & Strategy Switcher Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-indigo-400 border border-indigo-500/20">
              Interactive 3D Journey
            </span>
            <span className="text-xs text-slate-400">
              Multi-trajectory capital projection
            </span>
          </div>
          <h2 className="mt-1.5 text-xl sm:text-2xl font-extrabold tracking-tight text-white">
            Your Financial Journey
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Visualize your progression from current cash flow to goal milestones across alternative investment strategies.
          </p>
        </div>

        {/* Strategy Pathway Selector Chips */}
        {plans && plans.length > 0 && onSelectPlan && (
          <div className="flex items-center gap-2 bg-[#0d1322] p-1.5 rounded-xl border border-slate-800">
            {plans.map((p) => {
              const active = p.plan_id === selectedPlanId
              return (
                <button
                  key={p.plan_id}
                  type="button"
                  onClick={() => onSelectPlan(p.plan_id)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                    active
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <span className={`h-1.5 w-1.5 rounded-full ${
                    p.plan_id === 'A' ? 'bg-cyan-400' : p.plan_id === 'B' ? 'bg-indigo-400' : 'bg-emerald-400'
                  }`} />
                  <span>Plan {p.plan_id}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* 2. Main 3D Canvas / WebGL Visualization Container */}
      <div className="relative rounded-2xl border border-slate-800 bg-gradient-to-b from-[#080d18] via-[#0a0f1d] to-[#070b14] shadow-2xl overflow-hidden backdrop-blur-md">
        {/* Subtle Canvas Watermark Tag */}
        <div className="absolute top-3 left-3 z-10 pointer-events-none flex items-center gap-2 text-[10px] text-slate-400 bg-slate-950/70 px-2.5 py-1 rounded-lg border border-slate-800/80 backdrop-blur-sm">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
          <span>Rotate slightly to inspect path angles</span>
        </div>

        {/* 3D WebGL Canvas with Error Boundary and 2D Fallback */}
        <div className="h-72 sm:h-80 md:h-96 w-full">
          {isSupported ? (
            <WebGLErrorBoundary
              fallback={
                <FallbackJourney2D
                  profile={profile}
                  goals={goals}
                  plans={plans}
                  selectedPlanId={selectedPlanId}
                />
              }
            >
              <Canvas
                camera={{ position: [0, 1.8, 6.5], fov: 48 }}
                gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
              >
                <JourneyScene
                  plans={plans}
                  selectedPlanId={selectedPlanId}
                  goals={goals}
                  monthlySurplus={monthlySurplus}
                  prefersReducedMotion={prefersReducedMotion}
                />
              </Canvas>
            </WebGLErrorBoundary>
          ) : (
            <FallbackJourney2D
              profile={profile}
              goals={goals}
              plans={plans}
              selectedPlanId={selectedPlanId}
            />
          )}
        </div>
      </div>

      {/* 3. Concise High-Trust HTML Summary Panel */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        {/* Current Monthly Surplus */}
        <div className="rounded-xl bg-[#0d1322]/90 p-3.5 border border-slate-800 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Current Surplus</p>
          <p className="mt-1 text-base font-extrabold text-white">
            {formatINR(monthlySurplus)} <span className="text-xs font-normal text-slate-400">/ mo</span>
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400">Available cash flow baseline</p>
        </div>

        {/* Selected Strategy & Expected Return */}
        <div className="rounded-xl bg-[#0d1322]/90 p-3.5 border border-slate-800 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Selected Strategy</p>
          <p className="mt-1 text-base font-extrabold text-indigo-300 truncate">
            {selectedPlan ? `Plan ${selectedPlan.plan_id} (${selectedPlan.label})` : 'Plan A'}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400">
            {selectedPlan ? `${formatINR(selectedPlan.monthly_investment)}/mo commitment` : 'Monthly SIP'}
          </p>
        </div>

        {/* Primary Goal & Target */}
        <div className="rounded-xl bg-[#0d1322]/90 p-3.5 border border-slate-800 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Primary Goal</p>
          <p className="mt-1 text-base font-extrabold text-emerald-400 truncate">
            {primaryGoal ? formatINR(primaryGoal.target_amount) : '₹25,00,000'}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400 capitalize truncate">
            {primaryGoal ? `${primaryGoal.name?.replace(/_/g, ' ')} (${primaryGoal.years}y)` : 'Target Goal'}
          </p>
        </div>

        {/* Goal Success Probability */}
        <div className="rounded-xl bg-[#0d1322]/90 p-3.5 border border-slate-800 backdrop-blur-md">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Goal Success</p>
          <p className="mt-1 text-base font-extrabold text-white">
            {selectedPlan ? `${Math.round(selectedPlan.success_probability * 100)}%` : '87%'}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400">
            {selectedPlan?.survives_stress ? '✓ Survives Stress Shocks' : '⚠ Caution Under Stress'}
          </p>
        </div>
      </div>
    </section>
  )
}
