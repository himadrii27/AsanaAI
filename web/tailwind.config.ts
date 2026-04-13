import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        correct: "#00dc3c",
        incorrect: "#ff3c3c",
        accent: "#ffa500",
      },
    },
  },
  plugins: [],
};

export default config;
