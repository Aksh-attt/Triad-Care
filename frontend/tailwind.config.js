export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f4ff',
          100: '#dce8ff',
          500: '#2563eb',
          600: '#1d4ed8',
          700: '#1e3a8a',
          800: '#1e3366',
          900: '#172554',
        },
        teal: {
          500: '#0d9488',
          600: '#0f766e',
          700: '#115e59',
        },
        success: '#16a34a',
        warning: '#d97706',
        danger: '#dc2626',
      },
    },
  },
  plugins: [],
}
