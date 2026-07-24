/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0d0d",
        surface: "#131717",
        panel: "#181d1d",
        border: "#242b2b",
        "border-strong": "#333c3c",
        brand: "#18b2ba", // teal
        "brand-2": "#ce2f00", // deep orange-red (used sparingly)
        ink: "#e9eceb",
        muted: "#8fa0a0",
        faint: "#5b6666",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'Martian Mono'", "ui-monospace", "monospace"],
      },
      maxWidth: { content: "1180px" },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.02) inset, 0 12px 40px -18px rgba(0,0,0,0.8)",
      },
    },
  },
  plugins: [],
};
