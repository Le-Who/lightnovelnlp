import React from "react"
import { Monitor, Moon, Sun, Palette } from "lucide-react"
import { useTheme } from "./theme-provider"
import { Button } from "@/components/ui/Button"
import { cn } from "@/lib/utils"

export function ThemeToggle() {
  const { setTheme, theme } = useTheme()

  return (
    <div className="flex items-center justify-between gap-1 rounded-lg border bg-card p-1 shadow-sm">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setTheme("light")}
        className={cn("h-8 w-8", theme === "light" && "bg-secondary text-foreground")}
        title="Light Theme"
      >
        <Sun className="h-4 w-4" />
        <span className="sr-only">Light</span>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setTheme("dark")}
        className={cn("h-8 w-8", theme === "dark" && "bg-secondary text-foreground")}
        title="Dark Theme"
      >
        <Moon className="h-4 w-4" />
        <span className="sr-only">Dark</span>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setTheme("neutral")}
        className={cn("h-8 w-8", theme === "neutral" && "bg-secondary text-foreground")}
        title="Neutral Theme"
      >
        <Palette className="h-4 w-4" />
        <span className="sr-only">Neutral</span>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setTheme("system")}
        className={cn("h-8 w-8", theme === "system" && "bg-secondary text-foreground")}
        title="System Theme"
      >
        <Monitor className="h-4 w-4" />
        <span className="sr-only">System</span>
      </Button>
    </div>
  )
}
