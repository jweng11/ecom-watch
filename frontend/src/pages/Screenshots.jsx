import { useState, useEffect, useCallback, useRef } from "react"
import { api } from "@/lib/api"
import { Camera, Play, Loader2, X, ChevronLeft, ChevronRight, RefreshCw, ImageOff } from "lucide-react"

export function ScreenshotsPage() {
  const [screenshots, setScreenshots] = useState([])
  const [retailers, setRetailers] = useState([])
  const [scrapeStatus, setScrapeStatus] = useState({ running: false })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedRetailer, setSelectedRetailer] = useState("")
  const [selectedDate, setSelectedDate] = useState("")
  const [lightbox, setLightbox] = useState(null)
  const [scrapeMessage, setScrapeMessage] = useState(null)
  const pollRef = useRef(null)
  const mountedRef = useRef(true)

  // Track mounted state to prevent stale setTimeout updates
  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const loadData = useCallback(async () => {
    try {
      setError(null)
      const [screenshotRes, retailerRes, statusRes] = await Promise.all([
        api.getScreenshots({ retailer: selectedRetailer || undefined, date: selectedDate || undefined }),
        api.getRetailers(),
        api.getScrapeStatus(),
      ])
      setScreenshots(screenshotRes.screenshots || [])
      setRetailers(retailerRes.retailers || [])
      setScrapeStatus(statusRes)
    } catch (err) {
      setError(err.message || "Failed to load data")
    } finally {
      setLoading(false)
    }
  }, [selectedRetailer, selectedDate])

  useEffect(() => {
    setLoading(true)
    loadData()
  }, [loadData])

  // Poll scrape status while running
  useEffect(() => {
    if (scrapeStatus.running) {
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.getScrapeStatus()
          setScrapeStatus(status)
          if (!status.running) {
            clearInterval(pollRef.current)
            pollRef.current = null
            setScrapeMessage("Scrape completed!")
            loadData()
            setTimeout(() => { if (mountedRef.current) setScrapeMessage(null) }, 5000)
          }
        } catch {
          // ignore polling errors
        }
      }, 2000)
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [scrapeStatus.running, loadData])

  const handleScrape = async (retailer = "all") => {
    try {
      setScrapeMessage(null)
      await api.triggerScrape(retailer)
      setScrapeStatus({ running: true, current_retailer: null, progress: 0, retailers_completed: 0, retailers_total: 0 })
      setScrapeMessage(`Scrape started for ${retailer === "all" ? "all retailers" : retailer}...`)
    } catch (err) {
      setScrapeMessage(`Error: ${err.message}`)
      setTimeout(() => { if (mountedRef.current) setScrapeMessage(null) }, 5000)
    }
  }

  const uniqueDates = [...new Set(screenshots.map((s) => s.date))].sort().reverse()

  // Lightbox navigation
  const currentIndex = lightbox ? screenshots.findIndex((s) => s.path === lightbox.path) : -1
  const canPrev = currentIndex > 0
  const canNext = currentIndex < screenshots.length - 1

  // Keyboard navigation for lightbox (Escape, ArrowLeft, ArrowRight)
  useEffect(() => {
    if (!lightbox) return
    const handleKey = (e) => {
      if (e.key === "Escape") setLightbox(null)
      else if (e.key === "ArrowLeft" && currentIndex > 0) setLightbox(screenshots[currentIndex - 1])
      else if (e.key === "ArrowRight" && currentIndex < screenshots.length - 1) setLightbox(screenshots[currentIndex + 1])
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [lightbox, currentIndex, screenshots])

  if (error && !screenshots.length) {
    return (
      <div className="space-y-6">
        <Header onScrape={handleScrape} scrapeStatus={scrapeStatus} scrapeMessage={scrapeMessage} retailers={retailers} />
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center space-y-3 max-w-md">
            <p className="text-destructive font-medium">{error}</p>
            <button onClick={loadData} className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 cursor-pointer">
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Header onScrape={handleScrape} scrapeStatus={scrapeStatus} scrapeMessage={scrapeMessage} retailers={retailers} />

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={selectedRetailer}
          onChange={(e) => setSelectedRetailer(e.target.value)}
          className="px-3 py-2 border border-border rounded-lg text-sm bg-background"
          aria-label="Filter by retailer"
        >
          <option value="">All Retailers</option>
          {retailers.map((r) => (
            <option key={r.slug} value={r.slug}>{r.name}</option>
          ))}
        </select>
        <select
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="px-3 py-2 border border-border rounded-lg text-sm bg-background"
          aria-label="Filter by date"
        >
          <option value="">All Dates</option>
          {uniqueDates.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <button
          onClick={loadData}
          className="px-3 py-2 border border-border rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors cursor-pointer"
          aria-label="Refresh screenshots"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {/* Screenshot Grid */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : screenshots.length === 0 ? (
        <EmptyState onScrape={() => handleScrape("all")} hasRetailers={retailers.length > 0} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {screenshots.map((s) => (
            <button
              key={s.path}
              onClick={() => setLightbox(s)}
              className="group border border-border rounded-xl overflow-hidden hover:border-primary/50 transition-colors cursor-pointer bg-card"
            >
              <div className="aspect-[16/10] bg-muted relative overflow-hidden">
                <img
                  src={`/api/screenshots/${s.path}`}
                  alt={`${s.retailer} screenshot from ${s.date}`}
                  className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
              </div>
              <div className="px-3 py-2 flex items-center justify-between">
                <span className="text-sm font-medium capitalize">{s.retailer}</span>
                <span className="text-xs text-muted-foreground">{s.date}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Lightbox */}
      {lightbox && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Screenshot lightbox" onClick={() => setLightbox(null)}>
          <div className="relative max-w-6xl max-h-[90vh] w-full" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setLightbox(null)}
              className="absolute -top-10 right-0 text-white hover:text-white/80 cursor-pointer"
              aria-label="Close lightbox"
            >
              <X className="h-6 w-6" />
            </button>
            <div className="flex items-center justify-between text-white mb-2">
              <span className="text-sm font-medium capitalize">{lightbox.retailer} — {lightbox.date}</span>
              <span className="text-xs text-white/60">{((lightbox.size_bytes || 0) / 1024).toFixed(0)} KB</span>
            </div>
            <img
              src={`/api/screenshots/${lightbox.path}`}
              alt={`${lightbox.retailer} screenshot from ${lightbox.date}`}
              className="w-full max-h-[80vh] object-contain rounded-lg"
            />
            {canPrev && (
              <button
                onClick={() => setLightbox(screenshots[currentIndex - 1])}
                className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 cursor-pointer"
                aria-label="Previous screenshot"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
            )}
            {canNext && (
              <button
                onClick={() => setLightbox(screenshots[currentIndex + 1])}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 cursor-pointer"
                aria-label="Next screenshot"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


function Header({ onScrape, scrapeStatus, scrapeMessage, retailers }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Screenshots</h2>
        <p className="text-muted-foreground text-sm">Captured retailer promotion pages</p>
      </div>
      <div className="flex items-center gap-3">
        {scrapeStatus.running && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>
              {scrapeStatus.current_retailer
                ? `Scanning ${scrapeStatus.current_retailer}...`
                : "Starting scan..."}
              {scrapeStatus.retailers_total > 0 && (
                <span className="ml-1">({scrapeStatus.retailers_completed}/{scrapeStatus.retailers_total})</span>
              )}
            </span>
          </div>
        )}
        {scrapeMessage && !scrapeStatus.running && (
          <span className="text-sm text-muted-foreground">{scrapeMessage}</span>
        )}
        <div className="relative group">
          <button
            onClick={() => onScrape("all")}
            disabled={scrapeStatus.running}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <Play className="h-4 w-4" aria-hidden="true" />
            Scan All
          </button>
        </div>
        {/* Individual retailer scan dropdown */}
        <select
          onChange={(e) => { if (e.target.value) { onScrape(e.target.value); e.target.value = "" } }}
          disabled={scrapeStatus.running}
          className="px-3 py-2 border border-border rounded-lg text-sm bg-background disabled:opacity-50"
          aria-label="Scan individual retailer"
          defaultValue=""
        >
          <option value="" disabled>Scan one...</option>
          {retailers.filter((r) => r.scrape_enabled).map((r) => (
            <option key={r.slug} value={r.slug}>{r.name}</option>
          ))}
        </select>
      </div>
    </div>
  )
}


function EmptyState({ onScrape, hasRetailers }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center space-y-4 max-w-md">
        <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center">
          <ImageOff className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No screenshots yet</h3>
        <p className="text-sm text-muted-foreground">
          Run your first scan to capture retailer promotion pages. Screenshots are saved automatically for each retailer.
        </p>
        {hasRetailers && (
          <button
            onClick={onScrape}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 cursor-pointer"
          >
            <span className="flex items-center gap-2 justify-center">
              <Camera className="h-4 w-4" aria-hidden="true" />
              Run First Scan
            </span>
          </button>
        )}
      </div>
    </div>
  )
}
