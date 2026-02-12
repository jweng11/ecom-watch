import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import { formatCurrency, formatNumber } from "@/lib/utils"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Activity, DollarSign, Store, Users, CalendarRange } from "lucide-react"

const CHART_COLORS = {
  blue: "oklch(0.488 0.243 264.376)",
  green: "oklch(0.696 0.17 162.48)",
  orange: "oklch(0.769 0.188 70.08)",
  purple: "oklch(0.627 0.265 303.9)",
}

const tooltipStyle = {
  contentStyle: {
    background: "oklch(0.205 0 0)",
    border: "1px solid oklch(0.269 0 0)",
    borderRadius: 8,
    color: "oklch(0.985 0 0)",
    fontSize: 13,
  },
}

export function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [byRetailer, setByRetailer] = useState([])
  const [byVendor, setByVendor] = useState([])
  const [priceDist, setPriceDist] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  // [FIX] Use a counter to re-trigger fetch on retry instead of window.location.reload()
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([
      api.getSummary(),
      api.getByRetailer(),
      api.getByVendor(),
      api.getPriceDistribution(),
    ])
      .then(([s, r, v, p]) => {
        setSummary(s)
        setByRetailer(r || [])
        setByVendor((v || []).slice(0, 10))
        setPriceDist(p || [])
        setLoading(false)
      })
      .catch((err) => {
        console.error("Dashboard data fetch failed:", err)
        setError(err.message || "Failed to load dashboard data")
        setLoading(false)
      })
  }, [retryCount])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" role="status" aria-label="Loading dashboard">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  // [FIX] Error state UI
  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-3">
          <p className="text-lg font-semibold text-destructive-foreground">Failed to load dashboard</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
            onClick={() => setRetryCount((c) => c + 1)}
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // [FIX] Null-safe summary access
  if (!summary) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-muted-foreground">No data available</p>
      </div>
    )
  }

  const stats = [
    { label: "Total Promotions", value: formatNumber(summary.total_promotions), icon: Activity, color: "text-blue-400" },
    { label: "Avg Discount", value: `${summary.avg_discount_pct}%`, icon: DollarSign, color: "text-emerald-400" },
    { label: "Vendors Tracked", value: summary.total_vendors, icon: Users, color: "text-purple-400" },
    { label: "Promo Cycles", value: summary.total_cycles, icon: CalendarRange, color: "text-amber-400" },
    { label: "Retailers", value: summary.total_retailers, icon: Store, color: "text-rose-400" },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Overview of {formatNumber(summary.total_promotions)} laptop promotions &middot;{" "}
          {summary.date_range?.earliest || "N/A"} to {summary.date_range?.latest || "N/A"}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{s.label}</span>
                <s.icon className={`h-4 w-4 ${s.color}`} aria-hidden="true" />
              </div>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Promotions by Retailer</CardTitle>
          </CardHeader>
          <CardContent>
            {byRetailer.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer>
                  <BarChart data={byRetailer} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.269 0 0)" />
                    <XAxis type="number" stroke="oklch(0.5 0 0)" fontSize={12} />
                    <YAxis type="category" dataKey="retailer" stroke="oklch(0.5 0 0)" fontSize={12} width={85} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="count" fill={CHART_COLORS.blue} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">No retailer data available</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Price Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {priceDist.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer>
                  <BarChart data={priceDist}>
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.269 0 0)" />
                    <XAxis dataKey="band" stroke="oklch(0.5 0 0)" fontSize={12} />
                    <YAxis stroke="oklch(0.5 0 0)" fontSize={12} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="count" fill={CHART_COLORS.green} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">No price data available</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Top Vendors by Promotion Count</CardTitle>
          </CardHeader>
          <CardContent>
            {byVendor.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer>
                  <BarChart data={byVendor} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.269 0 0)" />
                    <XAxis type="number" stroke="oklch(0.5 0 0)" fontSize={12} />
                    <YAxis type="category" dataKey="vendor" stroke="oklch(0.5 0 0)" fontSize={12} width={85} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="count" fill={CHART_COLORS.purple} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">No vendor data available</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Avg Discount % by Retailer</CardTitle>
          </CardHeader>
          <CardContent>
            {byRetailer.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer>
                  <BarChart data={byRetailer}>
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.269 0 0)" />
                    <XAxis dataKey="retailer" stroke="oklch(0.5 0 0)" fontSize={12} />
                    <YAxis stroke="oklch(0.5 0 0)" fontSize={12} unit="%" />
                    <Tooltip {...tooltipStyle} formatter={(v) => v + "%"} />
                    <Bar dataKey="avg_discount_pct" fill={CHART_COLORS.orange} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">No discount data available</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
