import { useState, Component } from "react"
import { AppSidebar } from "@/components/AppSidebar"
import { DashboardPage } from "@/pages/Dashboard"
import { PromotionsPage } from "@/pages/Promotions"
import { TrendsPage } from "@/pages/Trends"
import { ComparisonPage } from "@/pages/Comparison"
import { ScreenshotsPage } from "@/pages/Screenshots"

// [FIX] Add Error Boundary to catch unhandled rendering errors
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4 max-w-md p-8">
            <div className="text-4xl">⚠</div>
            <h1 className="text-xl font-bold text-foreground">Something went wrong</h1>
            <p className="text-sm text-muted-foreground">
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <button
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try Again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

const pages = {
  dashboard: DashboardPage,
  promotions: PromotionsPage,
  trends: TrendsPage,
  comparison: ComparisonPage,
  screenshots: ScreenshotsPage,
}

export default function App() {
  const [activePage, setActivePage] = useState("dashboard")
  const PageComponent = pages[activePage] || DashboardPage

  return (
    <ErrorBoundary>
      <div className="flex min-h-screen bg-background">
        <AppSidebar activePage={activePage} onNavigate={setActivePage} />
        <main className="ml-56 flex-1 p-8">
          <ErrorBoundary key={activePage}>
            <PageComponent />
          </ErrorBoundary>
        </main>
      </div>
    </ErrorBoundary>
  )
}
