import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: "#67e8f9"
      },
      boxShadow: {
        panel: "0 18px 45px rgb(2 6 23 / 0.28)"
      }
    }
  },
  plugins: []
} satisfies Config;
