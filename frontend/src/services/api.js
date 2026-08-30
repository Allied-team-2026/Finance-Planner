/**
 * Cognizant Finance Planner API Service
 * Strictly adheres to docs/JSON_CONTRACT.md section 12.
 *
 * Every function here returns what the backend said, or throws. None of them
 * substitutes a default customer id: asking for the wrong customer's numbers is
 * worse than failing, because the screen still looks right.
 */

const API_BASE_URL = '' // Uses Vite proxy or relative path

export async function fetchPlan(requestPayload) {
  if (!requestPayload) {
    throw new Error('fetchPlan needs a request payload.')
  }

  try {
    const res = await fetch(`/api/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
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
  if (!customerId) {
    throw new Error('fetchChallenge needs a customer id.')
  }

  try {
    const res = await fetch(`/api/challenge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: customerId,
        chosen_plan_id: chosenPlanId,
      }),
    })

    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`)
    }

    // /api/challenge returns the whole section 11 response with the challenge
    // nested inside it. The caller wants the challenge, so unwrap it here rather
    // than in the component: the shape belongs to the API, not to the screen.
    const data = await res.json()
    if (!data || !data.challenge) {
      throw new Error('The backend returned no challenge for this plan.')
    }
    return data.challenge
  } catch (err) {
    console.error('[API Service] Challenge call failed.', err)
    throw err
  }
}

export async function fetchWhatIf(customerId, extraMonthlySavings) {
  if (!customerId) {
    throw new Error('fetchWhatIf needs a customer id.')
  }
  const extra = Number(extraMonthlySavings) || 0

  try {
    const res = await fetch(`/api/whatif`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: customerId,
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
