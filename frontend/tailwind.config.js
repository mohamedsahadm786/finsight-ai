/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary brand colors
        crimson: {
          DEFAULT: '#C62828',
          light: '#EF5350',
          dark: '#8E0000',
          glow: '#FF1744',
        },
        // Background layers
        void: '#05050A',
        surface: {
          DEFAULT: '#0D0D14',
          raised: '#12121C',
          overlay: '#181824',
        },
        // Accent
        electric: {
          DEFAULT: '#1565C0',
          light: '#42A5F5',
          glow: '#00B0FF',
        },
        // Risk tiers
        risk: {
          low: '#00E676',
          medium: '#FFD740',
          high: '#FF6D00',
          distress: '#D500F9',
        },
        // Text
        ink: {
          primary: '#F0F0F5',
          secondary: '#9090A8',
          muted: '#505068',
        },
      },
      fontFamily: {
        display: ['Orbitron', 'monospace'],
        body: ['Rajdhani', 'sans-serif'],
        mono: ['Courier New', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan': 'scan 8s linear infinite',
        'spin-slow': 'spin 8s linear infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px #C62828, 0 0 10px #C62828' },
          '100%': { boxShadow: '0 0 20px #C62828, 0 0 40px #C62828, 0 0 60px #C62828' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'crimson': '0 0 20px rgba(198, 40, 40, 0.4)',
        'crimson-lg': '0 0 40px rgba(198, 40, 40, 0.6)',
        'electric': '0 0 20px rgba(21, 101, 192, 0.4)',
        'inner-glow': 'inset 0 0 30px rgba(198, 40, 40, 0.1)',
      },
    },
  },
  plugins: [],
}