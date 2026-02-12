import { useState, useEffect, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select } from "@/components/ui/select"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { DiscountBadge } from "@/components/DiscountBadge"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

const C = {
  blue: "oklch(0.488 0.243 264.376)",
  green: "oklch(0.696 0.17 162.48)",
  orange: "oklch(0.769 0.188 70.08)",
  grid: "oklch(0.269 0 0)",
  axis: "oklch(0.5 0 0)",
}
const tt = { contentStyle: { background: "oklch(0.205 0 0)", border: "1px solid oklch(0.269 0 0)", borderRadius: 8, color: "oklch(0.985 0 0)", fontSize: 13 } }

export function ComparisonPage() {
  const [filters, setFilters] = useState(null)
  const [cycle, setCycle] = useState("")
  const [byRetailer, setByRetailer] = useState([])
  const [heatmap, setHeatmap] = useState([])
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
    const p = cycle ? { cycle } : {}
    // [FIX] Add .catch() to Promise.all
    Promise.all([api.getByRetailer(p), api.getHeatmap(p)])
      .then(([r, h]) => {
        setByRetailer(r || [])
        setHeatmap(h || [])
        setLoading(false)
      })
      .catch((err) => {
        console.error("Comparison fetch failed:", err)
        setError(err.message || "Failed to load comparison data")
        setLoading(false)
      })
  }, [cycle])

  const heatmapData = useMemo(() => {
    if (!heatmap || !heatmap.length) return { vendors: [], retailers: [], grid: {} }
    const vendors = [...new Set(heatmap.map((h) => h.vendor))].sort()
    const retailers = [...new Set(heatmap.map((h) => h.retailer))].sort()
    const grid = {}
    heatmap.forEach((h) => { grid[`${h.vendor}-${h.retailer}`] = h.count })
    return { vendors, retailers, grid }
  }, [heatmap])

  // [FIX] Safe maxCount - handle empty grid
  const maxCount = useMemo(() => {
    const values = Object.values(heatmapData.grid)
    return values.length > 0 ? Math.max(...values, 1) : 1
  }, [heatmapData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" role="status" aria-label="Loading comparison">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  // [FIX] Error state UI
  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-3">
          <p className="text-lg font-semibold text-destructive-foreground">Failed to load comparison</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Competitive Comparison</h1>
        <p className="text-sm text-muted-foreground">Compare retailer strategies and vendor distribution</p>
      </div>

      {filters && (
        <div className="flex items-center gap-3">
          <Select value={cycle} onChange={(e) => setCycle(e.target.value)} aria-label="Filter by cycle">
            <option value="">All Cycles</option>
            {(filters.cycles || []).map((c) => <option key={c} value={c}>{c}</option>)}
          </Select>
        </div>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Retailer Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          {byRetailer.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Retailer</TableHead>
                  <TableHead>Promotions</TableHead>
                  <TableHead>Avg Price</TableHead>
                  <TableHead>Avg Discount %</TableHead>
                  <TableHead>Min Price</TableHead>
                  <TableHead>Max Price</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {byRetailer.map((r) => (
                  <TableRow key={r.retailer}>
                    <TableCell><Badge variant="retailer">{r.retailer}</Badge></TableCell>
                    <TableCell className="font-semibold">{(r.count || 0).toLocaleString()}</TableCell>
                    <TableCell>{formatCurrency(r.avg_price)}</TableCell>
                    <TableCell><DiscountBadge pct={r.avg_discount_pct} /></TableCell>
                    <TableCell>{formatCurrency(r.min_price)}</TableCell>
                    <TableCell>{formatCurrency(r.max_price)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="py-8 text-center text-muted-foreground text-sm">No retailer data available for the selected cycle</div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Promotion Count by Retailer</CardTitle>
          </CardHeader>
          <CardContent>
            {byRetailer.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer>
                  <BarChart data={byRetailer}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                    <XAxis dataKey="retailer" stroke={C.axis} fontSize={12} />
                    <YAxis stroke={C.axis} fontSize={12} />
                    <Tooltip {...tt} />
                    <Bar dataKey="count" fill={C.blue} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">No data</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Avg Price & Discount by Retailer</CardTitle>
          </CardHeader>
          <CardContent>
            {byRetailer.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer>
                  <BarChart data={byRetailer}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
                    <XAxis dataKey="retailer" stroke={C.axis} fontSize={12} />
                    <YAxis yAxisId="price" stroke={C.axis} fontSize={12} tickFormatter={(v) => "$" + v} />
                    <YAxis yAxisId="pct" orientation="right" stroke={C.axis} fontSize={12} unit="%" />
                    <Tooltip {...tt} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar yAxisId="price" dataKey="avg_price" fill={C.green} radius={[4, 4, 0, 0]} name="Avg Price ($)" />
                    <Bar yAxisId="pct" dataKey="avg_discount_pct" fill={C.orange} radius={[4, 4, 0, 0]} name="Avg Discount (%)" />
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
          <CardTitle className="text-base">Vendor x Retailer Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          {heatmapData.vendors.length > 0 ? (
            <div className="overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Vendor</TableHead>
                    {heatmapData.retailers.map((r) => <TableHead key={r} className="text-center">{r}</TableHead>)}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {heatmapData.vendors.map((v) => (
                    <TableRow key={v}>
                      <TableCell><Badge variant="vendor">{v}</Badge></TableCell>
                      {heatmapData.retailers.map((r) => {
                        const count = heatmapData.grid[`${v}-${r}`] || 0
                        const intensity = count / maxCount
                        const bg = count > 0 ? `oklch(0.488 ${0.05 + intensity * 0.2} 264.376 / ${0.15 + intensity * 0.5})` : "transparent"
                        return (
                          <TableCell
                            key={r}
                            className="text-center font-medium"
                            style={{ background: bg, color: count > 0 ? "oklch(0.985 0 0)" : "oklch(0.4 0 0)" }}
                          >
                            {count || "\u2014"}
                          </TableCell>
                        )
                      })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-muted-foreground text-sm">No heatmap data available for the selected cycle</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
