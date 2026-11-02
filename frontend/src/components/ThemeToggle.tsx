import React from "react";
import type { ThemeMode, ResolvedTheme } from "../hooks/useTheme";

export interface ThemeToggleProps {
  theme: ThemeMode;
  resolvedTheme: ResolvedTheme;
  onCycle: () => void;
  className?: string;
}

export const ThemeToggle = React.memo(function ThemeToggle({
  theme,
  resolvedTheme,
  onCycle,
  className = "",
}: ThemeToggleProps) {
  const getLabel = () => {
    switch (theme) {
      case "dark":
        return "Theme: Dark";
      case "light":
        return "Theme: Light";
      case "system":
        return `Theme: Auto (${resolvedTheme})`;
    }
  };

  const getGlyph = () => {
    switch (theme) {
      case "dark":
        return "☾";
      case "light":
        return "☼";
      case "system":
        return "◐";
    }
  };

  return (
    <button
      type="button"
      className={`btn-theme-toggle ${className}`.trim()}
      onClick={onCycle}
      aria-label={`Current theme is ${theme}, showing ${resolvedTheme} mode. Click to cycle theme.`}
      title={`Theme: ${theme.toUpperCase()} (resolved: ${resolvedTheme})`}
    >
      <span className="theme-toggle-glyph" aria-hidden="true">
        {getGlyph()}
      </span>
      <span className="theme-toggle-text">{getLabel()}</span>
    </button>
  );
});
