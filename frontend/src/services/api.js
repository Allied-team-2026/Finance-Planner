import defaultApiResponse from '../data/api_response.json'

/**
 * Cognizant Finance Planner API Service
 * Strictly adheres to docs/JSON_CONTRACT.md section 12.
 */

const API_BASE_URL = '' // Uses Vite proxy or relative path

export async function fetchPlan(requestPayload) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload || { customer_id: 'C001' }),
    })

    if (res.ok) {
      return await res.json()
    }
  } catch (err) {
    console.warn('[API Service] Backend not reachable, using local contract mock payload.', err)
  }

  // Graceful offline fallback
  if (requestPayload && !requestPayload.customer_id) {
    // New User form submission offline fallback: adapt profile & goals from requestPayload
    const fallback = JSON.parse(JSON.stringify(defaultApiResponse))
    fallback.customer_name = 'New Customer'
    fallback.customer_id = `C-${Math.floor(100 + Math.random() * 900)}`
    fallback.context = {
      age: requestPayload.age,
      dependents: requestPayload.dependents,
      employment_type: requestPayload.employment_type,
      city_tier: requestPayload.city_tier,
    }
    const income = Number(requestPayload.monthly_income) || 0
    const expense = Number(requestPayload.monthly_expense) || 0
    const surplus = income - expense
    fallback.profile = {
      ...fallback.profile,
      monthly_income: income,
      monthly_expense: expense,
      monthly_surplus: surplus,
      net_worth: (Number(requestPayload.assets) || 0) - (Number(requestPayload.liabilities) || 0),
    }
    if (requestPayload.goals && requestPayload.goals.length > 0) {
      fallback.goals = requestPayload.goals
    }
    if (requestPayload.stated_risk) {
      fallback.risk = {
        ...fallback.risk,
        stated: requestPayload.stated_risk,
      }
    }
    return fallback
  }

  return defaultApiResponse
}

export async function fetchChallenge(customerId, chosenPlanId) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/challenge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: customerId || 'C001',
        chosen_plan_id: chosenPlanId,
      }),
    })

    if (res.ok) {
      return await res.json()
    }
  } catch (err) {
    console.warn('[API Service] Backend not reachable for challenge, using mock fallback.', err)
  }

  return null
}

export async function fetchWhatIf(customerId, extraMonthlySavings) {
  const extra = Number(extraMonthlySavings) || 0

  try {
    const res = await fetch(`${API_BASE_URL}/api/whatif`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: customerId || 'C001',
        extra_monthly_savings: extra,
      }),
    })

    if (res.ok) {
      return await res.json()
    }
  } catch (err) {
    console.warn('[API Service] Backend not reachable for what-if, using fallback.', err)
  }

  // Graceful fallback mimicking contract behavior when backend is offline
  const updated = JSON.parse(JSON.stringify(defaultApiResponse))
  if (updated.profile) {
    updated.profile.monthly_surplus = (updated.profile.monthly_surplus || 45000) + extra
  }
  if (updated.plans) {
    updated.plans = updated.plans.map((p) => {
      const surplusAfter = (updated.profile.monthly_surplus || 45000) - p.monthly_investment
      return {
        ...p,
        surplus_after_investment: surplusAfter,
        feasible: surplusAfter >= 0,
      }
    })
  }
  return updated
}

export async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/status`)
    if (res.ok) {
      return await res.json()
    }
  } catch {
    // Offline status
  }
  return {
    stages: {},
    engines_live: 0,
    stages_total: 11,
  }
}
