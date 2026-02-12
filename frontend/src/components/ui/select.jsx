import { cn } from "@/lib/utils"

function Select({ className, children, ...props }) {
  return (
    <select
      className={cn(
        "h-9 rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground shadow-sm transition-colors focus:outline-none focus:ring-1 focus:ring-ring",
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
}

export { Select }
