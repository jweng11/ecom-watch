import { Badge } from "@/components/ui/badge"

export function DiscountBadge({ pct }) {
  if (pct == null) return <span className="text-muted-foreground">{"\u2014"}</span>
  // [FIX] Handle negative or zero discount percentages
  if (pct <= 0) return <Badge variant="secondary">0%</Badge>
  const variant = pct >= 25 ? "destructive" : pct >= 15 ? "warning" : "success"
  return <Badge variant={variant}>{pct.toFixed(1)}%</Badge>
}
