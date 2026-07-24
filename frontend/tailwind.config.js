/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0d0d0f",
        surface: "#141416",
        panel: "#1a1a1d",
        border: "#262629",
        "border-strong": "#34343a",
        brand: "#3ecf8e",
        "brand-2": "#22d3ee",
        ink: "#f2f2f3",
        muted: "#9b9ba3",
        faint: "#6c6c75",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      maxWidth: { content: "1180px" },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.02) inset, 0 8px 24px -12px rgba(0,0,0,0.6)",
      },
    },
  },
  plugins: [],
};
