const API_BASE = 'http://localhost:8000/api';

export async function fetchPromotions(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') query.set(k, v);
  });
  const res = await fetch(`${API_BASE}/promotions?${query}`);
  return res.json();
}

export async function fetchFilters() {
  const res = await fetch(`${API_BASE}/promotions/filters`);
  return res.json();
}

export async function fetchSummary() {
  const res = await fetch(`${API_BASE}/analytics/summary`);
  return res.json();
}

export async function fetchByRetailer(cycle) {
  const params = cycle ? `?cycle=${cycle}` : '';
  const res = await fetch(`${API_BASE}/analytics/by-retailer${params}`);
  return res.json();
}

export async function fetchByVendor(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v) query.set(k, v);
  });
  const res = await fetch(`${API_BASE}/analytics/by-vendor?${query}`);
  return res.json();
}

export async function fetchDiscountTrends(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v) query.set(k, v);
  });
  const res = await fetch(`${API_BASE}/analytics/discount-trends?${query}`);
  return res.json();
}

export async function fetchPriceDistribution(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v) query.set(k, v);
  });
  const res = await fetch(`${API_BASE}/analytics/price-distribution?${query}`);
  return res.json();
}

export async function fetchVendorRetailerHeatmap(cycle) {
  const params = cycle ? `?cycle=${cycle}` : '';
  const res = await fetch(`${API_BASE}/analytics/vendor-retailer-heatmap${params}`);
  return res.json();
}
