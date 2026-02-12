import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { DiscountBadge } from "@/components/DiscountBadge"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, X } from "lucide-react"

// [FIX] Debounce hook to prevent API spam on search input
function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debouncedValue
}

export function PromotionsPage() {
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 0 })
  const [filters, setFilters] = useState(null)
  const [params, setParams] = useState({ page: 1, per_page: 50, sort_by: "week_date", sort_dir: "desc" })
  const [searchInput, setSearchInput] = useState("")
  const [loading, setLoading] = useState(true)
  // [FIX] Add error state
  const [error, setError] = useState(null)

  // [FIX] Debounce search input
  const debouncedSearch = useDebounce(searchInput, 300)

  useEffect(() => {
    api.getFilters()
      .then(setFilters)
      .catch((err) => console.error("Failed to load filters:", err))
  }, [])

  // [FIX] Sync debounced search to params
  useEffect(() => {
    setParams((p) => ({ ...p, search: debouncedSearch || undefined, page: 1 }))
  }, [debouncedSearch])

  useEffect(() => {
    setLoading(true)
    setError(null)
    api.getPromotions(params)
      .then((d) => {
        // [FIX] Null-safe data handling
        setData({
          items: d?.items || [],
          total: d?.total || 0,
          page: d?.page || 1,
          pages: d?.pages || 0,
        })
        setLoading(false)
      })
      .catch((err) => {
        console.error("Promotions fetch failed:", err)
        setError(err.message || "Failed to load promotions")
        setLoading(false)
      })
  }, [params])

  const updateFilter = (key, value) => setParams((p) => ({ ...p, [key]: value, page: 1 }))
  const setSort = (col) => {
    setParams((p) => ({
      ...p,
      sort_by: col,
      sort_dir: p.sort_by === col && p.sort_dir === "asc" ? "desc" : "asc",
    }))
  }
  const clearFilters = () => {
    setSearchInput("")
    setParams({ page: 1, per_page: 50, sort_by: "week_date", sort_dir: "desc" })
  }

  const SortHeader = ({ col, children }) => (
    <TableHead
      className="cursor-pointer select-none hover:text-foreground transition-colors"
      onClick={() => setSort(col)}
      role="columnheader"
      aria-sort={params.sort_by === col ? (params.sort_dir === "asc" ? "ascending" : "descending") : "none"}
    >
      <span className="flex items-center gap-1">
        {children}
        {params.sort_by === col && (
          <span className="text-primary" aria-hidden="true">{params.sort_dir === "asc" ? "▲" : "▼"}</span>
        )}
      </span>
    </TableHead>
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Promotions</h1>
        <p className="text-sm text-muted-foreground">{(data.total || 0).toLocaleString()} promotions found</p>
      </div>

      {filters && (
        <div className="flex items-center gap-3 flex-wrap">
          <Select value={params.retailer || ""} onChange={(e) => updateFilter("retailer", e.target.value)} aria-label="Filter by retailer">
            <option value="">All Retailers</option>
            {(filters.retailers || []).map((r) => <option key={r} value={r}>{r}</option>)}
          </Select>
          <Select value={params.vendor || ""} onChange={(e) => updateFilter("vendor", e.target.value)} aria-label="Filter by vendor">
            <option value="">All Vendors</option>
            {(filters.vendors || []).map((v) => <option key={v} value={v}>{v}</option>)}
          </Select>
          <Select value={params.cycle || ""} onChange={(e) => updateFilter("cycle", e.target.value)} aria-label="Filter by cycle">
            <option value="">All Cycles</option>
            {(filters.cycles || []).map((c) => <option key={c} value={c}>{c}</option>)}
          </Select>
          <Select value={params.form_factor || ""} onChange={(e) => updateFilter("form_factor", e.target.value)} aria-label="Filter by form factor">
            <option value="">All Form Factors</option>
            {(filters.form_factors || []).map((f) => <option key={f} value={f}>{f}</option>)}
          </Select>
          {/* [FIX] Debounced search — input drives local state, debounced value drives API */}
          <Input
            placeholder="Search SKU, CPU, notes..."
            className="w-52"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Search promotions"
          />
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="h-4 w-4 mr-1" aria-hidden="true" /> Clear
          </Button>
        </div>
      )}

      {/* [FIX] Error state */}
      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive-foreground">
          {error}
        </div>
      )}

      <Card className="overflow-hidden">
        <div className="overflow-auto max-h-[calc(100vh-320px)]">
          <Table>
            <TableHeader>
              <TableRow>
                <SortHeader col="week_date">Date</SortHeader>
                <SortHeader col="retailer">Retailer</SortHeader>
                <SortHeader col="vendor">Vendor</SortHeader>
                <TableHead>SKU</TableHead>
                <SortHeader col="msrp">MSRP</SortHeader>
                <SortHeader col="ad_price">Ad Price</SortHeader>
                <SortHeader col="discount">Discount</SortHeader>
                <TableHead>Disc %</TableHead>
                <TableHead>Cycle</TableHead>
                <TableHead>Form</TableHead>
                <TableHead>LCD</TableHead>
                <TableHead>CPU</TableHead>
                <TableHead>GPU</TableHead>
                <TableHead>RAM</TableHead>
                <TableHead>Storage</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={15} className="text-center py-12 text-muted-foreground">
                    <div className="flex items-center justify-center gap-2" role="status">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
                      Loading...
                    </div>
                  </TableCell>
                </TableRow>
              ) : data.items.length === 0 ? (
                /* [FIX] Empty state */
                <TableRow>
                  <TableCell colSpan={15} className="text-center py-12 text-muted-foreground">
                    No promotions found matching your filters. Try adjusting your search criteria.
                  </TableCell>
                </TableRow>
              ) : (
                data.items.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="text-muted-foreground">{p.week_date || "\u2014"}</TableCell>
                    <TableCell><Badge variant="retailer">{p.retailer}</Badge></TableCell>
                    <TableCell><Badge variant="vendor">{p.vendor}</Badge></TableCell>
                    <TableCell className="max-w-[200px] truncate" title={p.sku}>{p.sku}</TableCell>
                    <TableCell className="text-muted-foreground">{formatCurrency(p.msrp)}</TableCell>
                    <TableCell className="font-semibold">{formatCurrency(p.ad_price)}</TableCell>
                    <TableCell>{formatCurrency(p.discount)}</TableCell>
                    <TableCell><DiscountBadge pct={p.discount_pct} /></TableCell>
                    <TableCell>{p.cycle || "\u2014"}</TableCell>
                    <TableCell>{p.form_factor || "\u2014"}</TableCell>
                    <TableCell>{p.lcd_size || "\u2014"}</TableCell>
                    <TableCell className="max-w-[130px] truncate" title={p.cpu}>{p.cpu || "\u2014"}</TableCell>
                    <TableCell>{p.gpu || "\u2014"}</TableCell>
                    <TableCell>{p.ram || "\u2014"}</TableCell>
                    <TableCell>{p.storage || "\u2014"}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {data.items.length > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <p className="text-sm text-muted-foreground">
              Showing {((data.page - 1) * (params.per_page || 50)) + 1}–{Math.min(data.page * (params.per_page || 50), data.total)} of {data.total.toLocaleString()}
            </p>
            <nav className="flex items-center gap-1" aria-label="Pagination">
              <Button variant="outline" size="icon" disabled={data.page <= 1} onClick={() => setParams((p) => ({ ...p, page: 1 }))} aria-label="First page">
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" disabled={data.page <= 1} onClick={() => setParams((p) => ({ ...p, page: p.page - 1 }))} aria-label="Previous page">
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="px-3 text-sm text-muted-foreground">Page {data.page} of {data.pages}</span>
              <Button variant="outline" size="icon" disabled={data.page >= data.pages} onClick={() => setParams((p) => ({ ...p, page: p.page + 1 }))} aria-label="Next page">
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" disabled={data.page >= data.pages} onClick={() => setParams((p) => ({ ...p, page: data.pages }))} aria-label="Last page">
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </nav>
          </div>
        )}
      </Card>
    </div>
  )
}
