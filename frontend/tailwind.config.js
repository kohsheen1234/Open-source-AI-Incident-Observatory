/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#1c1c1c",
        surface: "#181818",
        panel: "#202020",
        border: "#2e2e2e",
        brand: "#3ecf8e",
        "brand-hover": "#34b87c",
        ink: "#ededed",
        muted: "#a0a0a0",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
