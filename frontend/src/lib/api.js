const BASE = "/api"

// [FIX] Add proper error handling — check res.ok and wrap in try/catch
class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function get(path, params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== "") query.set(k, v)
  })
  const sep = query.toString() ? "?" : ""
  // [FIX] Wrap fetch in try/catch to handle network errors (server unreachable, DNS failure)
  let res
  try {
    res = await fetch(`${BASE}${path}${sep}${query}`)
  } catch (networkError) {
    throw new ApiError(
      "Unable to connect to the server. Please check that the backend is running.",
      0
    )
  }
  if (!res.ok) {
    // [FIX] Try to extract detail from FastAPI error response body
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body.detail) detail = body.detail
    } catch {
      // response body wasn't JSON, use status text
    }
    throw new ApiError(`API error: ${detail}`, res.status)
  }
  return res.json()
}

export const api = {
  getPromotions: (p) => get("/promotions", p),
  getFilters: () => get("/promotions/filters"),
  getSummary: () => get("/analytics/summary"),
  getByRetailer: (p) => get("/analytics/by-retailer", p),
  getByVendor: (p) => get("/analytics/by-vendor", p),
  getDiscountTrends: (p) => get("/analytics/discount-trends", p),
  getPriceDistribution: (p) => get("/analytics/price-distribution", p),
  getHeatmap: (p) => get("/analytics/vendor-retailer-heatmap", p),
}
