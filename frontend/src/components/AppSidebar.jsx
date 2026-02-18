import { cn } from "@/lib/utils"
import { LayoutDashboard, Table2, TrendingUp, GitCompareArrows, Camera, Bell, Settings, ScanSearch } from "lucide-react"

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, section: "Overview" },
  { id: "promotions", label: "Promotions", icon: Table2, section: "Data" },
  { id: "trends", label: "Trends", icon: TrendingUp, section: "Analysis" },
  { id: "comparison", label: "Comparison", icon: GitCompareArrows, section: "Analysis" },
  { id: "screenshots", label: "Screenshots", icon: Camera, section: "Scraping" },
]

const comingSoon = [
  { label: "Review Queue", icon: ScanSearch },
  { label: "Alerts", icon: Bell },
  { label: "Settings", icon: Settings },
]

export function AppSidebar({ activePage, onNavigate }) {
  let lastSection = ""
  return (
    <aside className="w-56 border-r border-border bg-sidebar flex flex-col fixed h-screen overflow-y-auto">
      <div className="px-5 py-5">
        <h1 className="text-lg font-bold text-sidebar-primary tracking-tight">Ecom-Watch</h1>
        <p className="text-xs text-muted-foreground">Laptop Promotion Intel</p>
      </div>

      <nav className="flex-1 px-3 space-y-0.5">
        {navItems.map((item) => {
          const showSection = item.section !== lastSection
          lastSection = item.section
          return (
            <div key={item.id}>
              {showSection && (
                <p className="px-3 pt-4 pb-1 text-[11px] uppercase tracking-widest text-muted-foreground/60 font-medium">
                  {item.section}
                </p>
              )}
              <button
                onClick={() => onNavigate(item.id)}
                aria-current={activePage === item.id ? "page" : undefined}
                className={cn(
                  "w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors cursor-pointer",
                  activePage === item.id
                    ? "bg-sidebar-primary text-sidebar-primary-foreground font-medium"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <item.icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </button>
            </div>
          )
        })}

        <p className="px-3 pt-6 pb-1 text-[11px] uppercase tracking-widest text-muted-foreground/60 font-medium">
          Coming Soon
        </p>
        {comingSoon.map((item) => (
          <div
            key={item.label}
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground/40"
            aria-disabled="true"
          >
            <item.icon className="h-4 w-4" aria-hidden="true" />
            {item.label}
          </div>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-border">
        <p className="text-[11px] text-muted-foreground/50">Phase 2 — v0.2.0</p>
      </div>
    </aside>
  )
}
