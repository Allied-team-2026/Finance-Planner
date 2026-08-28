/**
 * Pure Display Formatters for Finance-Planner Frontend.
 *
 * CRITICAL RULE:
 * The frontend NEVER calculates, derives, or infers numbers.
 * Every value displayed comes strictly from the API response and is ONLY formatted for display.
 * Null values represent "not applicable" and must strictly format as "—" (never 0 or "").
 */

/**
 * Format a number into Indian Rupees currency string (e.g. ₹25,00,000).
 *
 * @param {number|null|undefined} value - Raw monetary amount in integer rupees.
 * @returns {string} Formatted Indian Rupee string or "—" if null/undefined.
 */
export function formatRupees(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return "—";
  }
  const isNegative = value < 0;
  const absValue = Math.abs(Math.round(value));
  
  // Format with standard Indian numbering system grouping (e.g. 12,34,567)
  const str = absValue.toString();
  let result = "";
  if (str.length > 3) {
    const lastThree = str.substring(str.length - 3);
    const otherNumbers = str.substring(0, str.length - 3);
    result = otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + lastThree;
  } else {
    result = str;
  }

  return (isNegative ? "-₹" : "₹") + result;
}

/**
 * Format a decimal fraction (0.0 - 1.0) into a percentage string (e.g. 0.82 -> 82%).
 *
 * @param {number|null|undefined} value - Decimal rate or probability.
 * @param {number} decimals - Number of decimal digits to display (default 0).
 * @returns {string} Formatted percentage or "—" if null/undefined.
 */
export function formatPercent(value, decimals = 0) {
  if (value === null || value === undefined || isNaN(value)) {
    return "—";
  }
  const pct = (Number(value) * 100).toFixed(decimals);
  // Remove trailing .0 if present and decimals == 0
  return `${pct}%`;
}

/**
 * Format a standard integer/float with Indian locale separators.
 *
 * @param {number|null|undefined} value
 * @returns {string}
 */
export function formatNumber(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return "—";
  }
  return new Intl.NumberFormat("en-IN").format(value);
}

/**
 * Format a decimal or count metric safely with units.
 *
 * @param {number|string|null|undefined} value
 * @param {string} unit
 * @returns {string}
 */
export function formatMetric(value, unit = "") {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return unit ? `${value} ${unit}` : `${value}`;
}
