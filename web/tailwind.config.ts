import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0b0c0f",
        panel: "#13151a",
        edge: "#23262d",
        accent: "#f59e0b",
      },
    },
  },
  plugins: [],
};

export default config;
