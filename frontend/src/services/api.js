import defaultApiResponse from '../data/api_response.json'

/**
 * Cognizant Finance Planner API Service
 * Strictly adheres to docs/JSON_CONTRACT.md section 12.
 */

const API_BASE_URL = '' // Uses Vite proxy or relative path

export async function fetchPlan(requestPayload) {
  try {
    const res = await fetch(`/api/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload || { customer_id: 'C001' }),
    })

    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`)
    }
    return await res.json()
  } catch (err) {
    console.error('[API Service] Backend not reachable.', err)
    throw new Error('Connection error: Unable to reach the backend. Please ensure the backend is running.')
  }
}

export async function fetchCustomerProfile(customerId) {
  try {
    const res = await fetch(`/api/customer/${customerId}`)
    if (!res.ok) {
      if (res.status === 404) return null
      throw new Error(`API Error: ${res.status}`)
    }
    return await res.json()
  } catch (err) {
    console.error('[API Service] Backend not reachable for customer fetch.', err)
    throw err
  }
}

export async function fetchChallenge(customerId, chosenPlanId) {
  try {
    const res = await fetch(`/api/challenge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: customerId || 'C001',
        chosen_plan_id: chosenPlanId,
      }),
    })

    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`)
    }
    return await res.json()
  } catch (err) {
    console.error('[API Service] Backend not reachable for challenge.', err)
    throw new Error('Connection error: Unable to reach the backend.')
  }
}

export async function fetchWhatIf(customerId, extraMonthlySavings) {
  const extra = Number(extraMonthlySavings) || 0

  try {
    const res = await fetch(`/api/whatif`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: customerId || 'C001',
        extra_monthly_savings: extra,
      }),
    })

    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`)
    }
    return await res.json()
  } catch (err) {
    console.error('[API Service] Backend not reachable for what-if.', err)
    throw new Error('Connection error: Unable to reach the backend.')
  }
}

export async function fetchStatus() {
  try {
    const res = await fetch(`/api/status`)
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
