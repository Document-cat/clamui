/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,ts,jsx,tsx,md,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        clam: {
          forest: "#3d7a4e",
          "forest-deep": "#2d5c3a",
          sage: "#a8c9b0",
          "sage-pale": "#e0ede3",
          slate: "#2c3e50",
          "slate-deep": "#1a2634",
          "slate-ink": "#0f1721",
          sky: "#3498db",
          "sky-deep": "#2980b9",
          amber: "#e0b657",
        },
      },
      fontFamily: {
        sans: [
          "Cantarell",
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        window:
          "0 1px 2px rgba(0,0,0,0.15), 0 8px 24px -8px rgba(0,0,0,0.35), 0 32px 64px -24px rgba(0,0,0,0.45)",
        glow: "0 0 0 1px rgba(61,122,78,0.4), 0 0 48px -8px rgba(61,122,78,0.45)",
      },
      keyframes: {
        "scan-sweep": {
          "0%": { transform: "translateY(-100%)", opacity: "0" },
          "15%": { opacity: "0.8" },
          "85%": { opacity: "0.8" },
          "100%": { transform: "translateY(100%)", opacity: "0" },
        },
        "caret-blink": {
          "0%,49%": { opacity: "1" },
          "50%,100%": { opacity: "0" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "scan-sweep": "scan-sweep 2.4s ease-in-out 1",
        "caret-blink": "caret-blink 1.1s steps(1) infinite",
        "fade-up": "fade-up 0.7s ease-out both",
      },
    },
  },
  plugins: [],
};
