import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(val) {
  if (val == null) return "\u2014"
  // [FIX] Guard against NaN from non-numeric values
  const num = Number(val)
  if (Number.isNaN(num)) return "\u2014"
  return "$" + num.toLocaleString("en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function formatNumber(val) {
  if (val == null) return "\u2014"
  // [FIX] Guard against NaN
  const num = Number(val)
  if (Number.isNaN(num)) return "\u2014"
  return num.toLocaleString("en-CA")
}
