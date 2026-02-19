import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"
import { ArrowLeft, Check, X, RefreshCw } from "lucide-react"

export function ReviewQueuePage() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [promotions, setPromotions] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingCell, setEditingCell] = useState(null)

  useEffect(() => { loadPending() }, [])

  async function loadPending() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getReviewPending()
      setRuns(data.runs || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadRunPromotions(runId) {
    setLoading(true)
    try {
      const data = await api.getReviewRunPromotions(runId)
      setSelectedRun(data.scrape_run)
      setPromotions(data.promotions || [])
      setSelected(new Set())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleBulkAction(action) {
    if (selected.size === 0) return
    const ids = [...selected]
    try {
      if (action === "approve") {
        await api.reviewApprove(ids)
      } else {
        await api.reviewReject(ids)
      }
      setPromotions(prev => prev.filter(p => !selected.has(p.id)))
      setSelected(new Set())
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleReextract(runId) {
    setLoading(true)
    try {
      await api.reviewReextract(runId)
      await loadRunPromotions(runId)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function toggleSelect(id) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selected.size === promotions.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(promotions.map(p => p.id)))
    }
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Review Queue</h1>
        <Card><CardContent className="p-6 text-center text-red-500">{error}</CardContent></Card>
      </div>
    )
  }

  // Run detail view
  if (selectedRun) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => { setSelectedRun(null); loadPending() }}>
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <h1 className="text-2xl font-bold">Review: {selectedRun.retailer}</h1>
          <Badge variant="outline">{promotions.length} pending</Badge>
        </div>

        <div className="flex gap-2">
          <Button size="sm" onClick={toggleAll} variant="outline">
            {selected.size === promotions.length ? "Deselect All" : "Select All"}
          </Button>
          <Button size="sm" onClick={() => handleBulkAction("approve")} disabled={selected.size === 0}
            className="bg-green-600 hover:bg-green-700 text-white">
            <Check className="h-4 w-4 mr-1" /> Approve ({selected.size})
          </Button>
          <Button size="sm" onClick={() => handleBulkAction("reject")} disabled={selected.size === 0}
            variant="destructive">
            <X className="h-4 w-4 mr-1" /> Reject ({selected.size})
          </Button>
          <Button size="sm" onClick={() => handleReextract(selectedRun.id)} variant="outline">
            <RefreshCw className="h-4 w-4 mr-1" /> Re-extract
          </Button>
        </div>

        <Card>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10"></TableHead>
                  <TableHead>Vendor</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead className="text-right">MSRP</TableHead>
                  <TableHead className="text-right">Ad Price</TableHead>
                  <TableHead className="text-right">Discount</TableHead>
                  <TableHead>CPU</TableHead>
                  <TableHead>RAM</TableHead>
                  <TableHead>Storage</TableHead>
                  <TableHead>Screen</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {promotions.map(p => (
                  <TableRow key={p.id} className={selected.has(p.id) ? "bg-primary/5" : ""}>
                    <TableCell>
                      <input type="checkbox" checked={selected.has(p.id)}
                        onChange={() => toggleSelect(p.id)} className="cursor-pointer" />
                    </TableCell>
                    <TableCell className="font-medium">{p.vendor}</TableCell>
                    <TableCell className="max-w-[300px] truncate text-xs">{p.sku}</TableCell>
                    <TableCell className="text-right">{p.msrp ? formatCurrency(p.msrp) : "—"}</TableCell>
                    <TableCell className="text-right font-medium text-green-600">
                      {p.ad_price ? formatCurrency(p.ad_price) : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      {p.discount ? `${formatCurrency(p.discount)} (${p.discount_pct?.toFixed(0)}%)` : "—"}
                    </TableCell>
                    <TableCell className="text-xs">{p.cpu || "—"}</TableCell>
                    <TableCell className="text-xs">{p.ram || "—"}</TableCell>
                    <TableCell className="text-xs">{p.storage || "—"}</TableCell>
                    <TableCell className="text-xs">{p.lcd_size || "—"}</TableCell>
                  </TableRow>
                ))}
                {promotions.length === 0 && (
                  <TableRow><TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
                    No pending promotions
                  </TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>
    )
  }

  // Runs list view
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Review Queue</h1>
      <p className="text-muted-foreground">AI-extracted promotions awaiting human review</p>

      {loading ? (
        <Card><CardContent className="p-6 text-center text-muted-foreground">Loading...</CardContent></Card>
      ) : runs.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-muted-foreground">
          No pending reviews. Run a scrape to populate the queue.
        </CardContent></Card>
      ) : (
        <div className="grid gap-4">
          {runs.map(run => (
            <Card key={run.scrape_run_id} className="cursor-pointer hover:border-primary/50 transition-colors"
              onClick={() => loadRunPromotions(run.scrape_run_id)}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium">{run.retailer}</p>
                  <p className="text-sm text-muted-foreground">
                    {run.started_at ? new Date(run.started_at).toLocaleString() : "Unknown date"}
                  </p>
                </div>
                <Badge variant="secondary">{run.pending_count} pending</Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
