import { useState, useEffect, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"
import { ArrowLeft, Check, X, RefreshCw, Pencil } from "lucide-react"

// Editable fields and their display types
const EDITABLE_FIELDS = {
  vendor: { label: "Vendor", type: "text" },
  sku: { label: "SKU", type: "text" },
  msrp: { label: "MSRP", type: "number" },
  ad_price: { label: "Ad Price", type: "number" },
  cpu: { label: "CPU", type: "text" },
  ram: { label: "RAM", type: "text" },
  storage: { label: "Storage", type: "text" },
  lcd_size: { label: "Screen", type: "text" },
  gpu: { label: "GPU", type: "text" },
  resolution: { label: "Resolution", type: "text" },
  form_factor: { label: "Form Factor", type: "text" },
  os: { label: "OS", type: "text" },
  promo_type: { label: "Promo Type", type: "text" },
  notes: { label: "Notes", type: "text" },
}

function EditableCell({ value, field, promoId, onSave }) {
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(value ?? "")
  const fieldConfig = EDITABLE_FIELDS[field]
  const isNumber = fieldConfig?.type === "number"

  function handleDoubleClick() {
    setEditValue(value ?? "")
    setEditing(true)
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") {
      commitEdit()
    } else if (e.key === "Escape") {
      setEditing(false)
    }
  }

  function commitEdit() {
    setEditing(false)
    const newValue = isNumber
      ? (editValue === "" ? null : parseFloat(editValue))
      : (editValue === "" ? null : editValue)
    if (newValue !== value) {
      onSave(promoId, field, newValue)
    }
  }

  if (editing) {
    return (
      <Input
        type={isNumber ? "number" : "text"}
        step={isNumber ? "0.01" : undefined}
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onBlur={commitEdit}
        onKeyDown={handleKeyDown}
        autoFocus
        className="h-7 text-xs min-w-[80px]"
      />
    )
  }

  return (
    <span
      onDoubleClick={handleDoubleClick}
      className="cursor-pointer hover:bg-muted/50 px-1 py-0.5 rounded inline-block min-w-[30px]"
      title="Double-click to edit"
    >
      {value ?? "—"}
    </span>
  )
}

export function ReviewQueuePage() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [promotions, setPromotions] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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

  const handleCellSave = useCallback(async (promoId, field, newValue) => {
    try {
      const updated = await api.reviewUpdate(promoId, { [field]: newValue })
      setPromotions(prev =>
        prev.map(p => (p.id === promoId ? { ...p, ...updated } : p))
      )
    } catch (e) {
      setError(`Failed to update: ${e.message}`)
    }
  }, [])

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
        <Card>
          <CardContent className="p-6 text-center text-red-500">
            {error}
            <Button variant="outline" size="sm" className="ml-4" onClick={() => { setError(null); loadPending() }}>
              Retry
            </Button>
          </CardContent>
        </Card>
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
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Pencil className="h-3 w-3" /> Double-click cells to edit
          </span>
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
                    <TableCell className="font-medium">
                      <EditableCell value={p.vendor} field="vendor" promoId={p.id} onSave={handleCellSave} />
                    </TableCell>
                    <TableCell className="max-w-[300px] text-xs">
                      <EditableCell value={p.sku} field="sku" promoId={p.id} onSave={handleCellSave} />
                    </TableCell>
                    <TableCell className="text-right">
                      <EditableCell
                        value={p.msrp}
                        field="msrp"
                        promoId={p.id}
                        onSave={handleCellSave}
                      />
                    </TableCell>
                    <TableCell className="text-right font-medium text-green-600">
                      <EditableCell
                        value={p.ad_price}
                        field="ad_price"
                        promoId={p.id}
                        onSave={handleCellSave}
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      {p.discount ? `${formatCurrency(p.discount)} (${p.discount_pct?.toFixed(0)}%)` : "—"}
                    </TableCell>
                    <TableCell className="text-xs">
                      <EditableCell value={p.cpu} field="cpu" promoId={p.id} onSave={handleCellSave} />
                    </TableCell>
                    <TableCell className="text-xs">
                      <EditableCell value={p.ram} field="ram" promoId={p.id} onSave={handleCellSave} />
                    </TableCell>
                    <TableCell className="text-xs">
                      <EditableCell value={p.storage} field="storage" promoId={p.id} onSave={handleCellSave} />
                    </TableCell>
                    <TableCell className="text-xs">
                      <EditableCell value={p.lcd_size} field="lcd_size" promoId={p.id} onSave={handleCellSave} />
                    </TableCell>
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
