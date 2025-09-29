/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ftc-blue': '#0066cc',
        'ftc-red': '#ff4d4d',
        'grid-blue': '#00bcff',
      }
    },
  },
  plugins: [],
}