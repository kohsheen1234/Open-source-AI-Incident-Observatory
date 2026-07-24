/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0806",
        surface: "#14100c",
        panel: "#1b1611",
        border: "#2b241c",
        "border-strong": "#3b3125",
        brand: "#f5a524", // spice amber
        "brand-2": "#ff7a18", // ember orange
        ink: "#f6efe4",
        muted: "#a89f90",
        faint: "#6f665a",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      maxWidth: { content: "1180px" },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 12px 40px -18px rgba(0,0,0,0.8)",
      },
    },
  },
  plugins: [],
};
