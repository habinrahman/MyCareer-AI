import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-geist-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        /** MicroDegree brand (aligned with marketing site — not generic Tailwind reds) */
        microRed: "#EF4444",
        microRedLight: "#F87171",
        microRedSoft: "#FCA5A5",
        microRedDark: "#DC2626",
        microBlue: "#2563EB",
        microBlueLight: "#3B82F6",
        microGray: "#F9FAFB",
        microGrayMuted: "#F3F4F6",
        microText: "#111827",
        microTextSecondary: "#374151",
        microMuted: "#6B7280",
        microLight: "#9CA3AF",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        brand: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9",
          600: "#0284c7",
          900: "#0c4a6e",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        /** 12px — cards / controls */
        micro: "12px",
        /** 16px — hero panels / large surfaces */
        "micro-lg": "16px",
      },
      boxShadow: {
        micro: "0 4px 20px rgba(0, 0, 0, 0.08)",
        "micro-lg": "0 10px 30px rgba(0, 0, 0, 0.12)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
