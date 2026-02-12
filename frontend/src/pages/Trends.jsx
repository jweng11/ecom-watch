import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { api } from "@/lib/api"
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const C = {
  green: "oklch(0.696 0.17 162.48)",
  blue: "oklch(0.488 0.243 264.376)",
  purple: "oklch(0.627 0.265 303.9)",
  orange: "oklch(0.769 0.188 70.08)",
  grid: "oklch(0.269 0 0)",
  axis: "oklch(0.5 0 0)",
}
const tt = { contentStyle: { background: "oklch(0.205 0 0)", border: "1px solid oklch(0.269 0 0)", borderRadius: 8, color: "oklch(0.985 0 0)", fontSize: 13 } }

export function TrendsPage() {
  const [trends, setTrends] = useState([])
  const [filters, setFilters] = useState(null)
  const [retailer, setRetailer] = useState("")
  const [vendor, setVendor] = useState("")
  const [loading, setLoading] = useState(true)
  // [FIX] Add error state
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getFilters()
      .then(setFilters)
      .catch((err) => console.error("Failed to load filters:", err))
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    api.getDiscountTrends({ retailer, vendor })
      .then((d) => { setTrends(d || []); setLoading(false) })
      .catch((err) => {
        console.error("Trends fetch failed:", err)
        setError(err.message || "Failed to load trend data")
        setLoading(false)
      })
  }, [retailer, vendor])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" role="status" aria-label="Loading trends">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  // [FIX] Error state UI
  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-3">
          <p className="text-lg font-semibold text-destructive-foreground">Failed to load trends</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Trend Analysis</h1>
        <p className="text-sm text-muted-foreground">Discount and pricing trends across promotional cycles</p>
      </div>

      {filters && (
        <div className="flex items-center gap-3">
          <Select value={retailer} onChange={(e) => setRetailer(e.target.value)} aria-label="Filter by retailer">
            <option value="">All Retailers</option>
            {(filters.retailers || []).map((r) => <option key={r} value={r}>{r}</option>)}
          </Select>
          <Select value={vendor} onChange={(e) => setVendor(e.target.value)} aria-label="Filter by vendor">
            <option value="">All Vendors</option>
            {(filters.vendors || []).map((v) => <option key={v} value={v}>{v}</option>)}
          </Select>
        </div>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Average Discount % by Cycle</CardTitle>
        </CardHeader>
        <CardContent>
          {trends.length > 0 ? (
            <div className="h-[380px]">
              <ResponsiveContainer>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                  <XAxis dataKey="cycle" stroke={C.axis} fontSize={11} angle={-30} textAnchor="end" height={55} />
                  <YAxis stroke={C.axis} fontSize={12} unit="%" />
                  <Tooltip {...tt} formatter={(v) => (typeof v === "number" ? v.toFixed(1) : v) + "%"} />
                  <Line type="monotone" dataKey="avg_discount_pct" stroke={C.green} strokeWidth={2.5} dot={{ fill: C.green, r: 4 }} name="Avg Discount %" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[380px] flex items-center justify-center text-muted-foreground text-sm">No trend data available for the selected filters</div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Average Ad Price by Cycle</CardTitle>
          </CardHeader>
          <CardContent>
            {trends.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer>
                  <LineChart data={trends}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                    <XAxis dataKey="cycle" stroke={C.axis} fontSize={11} angle={-30} textAnchor="end" height={55} />
                    <YAxis stroke={C.axis} fontSize={12} tickFormatter={(v) => "$" + v} />
                    <Tooltip {...tt} formatter={(v) => "$" + (typeof v === "number" ? v.toFixed(2) : v)} />
                    <Line type="monotone" dataKey="avg_price" stroke={C.blue} strokeWidth={2.5} dot={{ fill: C.blue, r: 4 }} name="Avg Price" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">No data</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Promotion Count by Cycle</CardTitle>
          </CardHeader>
          <CardContent>
            {trends.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer>
                  <BarChart data={trends}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                    <XAxis dataKey="cycle" stroke={C.axis} fontSize={11} angle={-30} textAnchor="end" height={55} />
                    <YAxis stroke={C.axis} fontSize={12} />
                    <Tooltip {...tt} />
                    <Bar dataKey="count" fill={C.purple} radius={[4, 4, 0, 0]} name="# Promotions" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">No data</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Average Discount ($) by Cycle</CardTitle>
        </CardHeader>
        <CardContent>
          {trends.length > 0 ? (
            <div className="h-[280px]">
              <ResponsiveContainer>
                <BarChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                  <XAxis dataKey="cycle" stroke={C.axis} fontSize={11} angle={-30} textAnchor="end" height={55} />
                  <YAxis stroke={C.axis} fontSize={12} tickFormatter={(v) => "$" + v} />
                  <Tooltip {...tt} formatter={(v) => "$" + (typeof v === "number" ? v.toFixed(2) : v)} />
                  <Bar dataKey="avg_discount_dollars" fill={C.orange} radius={[4, 4, 0, 0]} name="Avg Discount $" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[280px] flex items-center justify-center text-muted-foreground text-sm">No data</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
