/**
 * Demo credentials configuration for hackathon evaluation and demonstration.
 * Maps the 3 existing customer personas (C001, C002, C003) to demo passwords.
 */
export const DEMO_CREDENTIALS = {
  C001: {
    customerId: 'C001',
    customerName: 'Rahul Mehta',
    password: 'demoPassword123',
    profileSummary: 'Age 28 · Salaried · Metro · Aggressive Profile',
  },
  C002: {
    customerId: 'C002',
    customerName: 'Vihaan Sharma',
    password: 'demoPassword123',
    profileSummary: 'Age 39 · Salaried · Tier 3 · Conservative Profile',
  },
  C003: {
    customerId: 'C003',
    customerName: 'Vivaan Patel',
    password: 'demoPassword123',
    profileSummary: 'Age 31 · Self-Employed · Tier 3 · Aggressive Profile',
  },
}

/**
 * Validates provided credentials against demo customer profiles.
 *
 * @param {string} customerId - The customer ID entered by the user.
 * @param {string} password - The password entered by the user.
 * @returns {{ isValid: boolean, error?: string, customer?: object }} Validation result.
 */
export function validateCredentials(customerId, password) {
  if (!customerId || !customerId.trim()) {
    return {
      isValid: false,
      error: 'Please enter your Customer ID.',
    }
  }

  if (!password) {
    return {
      isValid: false,
      error: 'Please enter your password.',
    }
  }

  const normalizedId = customerId.trim().toUpperCase()
  const account = DEMO_CREDENTIALS[normalizedId]

  if (!account) {
    return {
      isValid: false,
      error: `Customer ID "${customerId.trim()}" not recognized. Valid demo accounts: C001, C002, C003.`,
    }
  }

  const trimmedPass = password.trim()
  if (trimmedPass !== account.password && trimmedPass !== 'demo123') {
    return {
      isValid: false,
      error: 'Invalid password for this customer account. Please try again.',
    }
  }

  return {
    isValid: true,
    customer: account,
  }
}
