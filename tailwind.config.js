/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Activation du mode sombre via classe CSS
  content: [
    "./templates/**/*.html",
    "./templates/*.html",
    "./static/js/**/*.js",
    "./app.py",
    "./models.py",
  ],
  theme: {
    extend: {
      colors: {
        // Mode clair
        'lime': '#84CC16',
        'ivory': '#FFFBEA',
        'pearl': '#D1D5DB',
        'coral': '#FB7185',
        'sage': '#A7F3D0',
        'solar': '#FACC15',
        'plum': '#7C3AED',
        
        // Mode sombre
        'dark-bg': '#0F172A',
        'dark-surface': '#1E293B',
        'dark-surface-lighter': '#334155',
        'dark-border': '#475569',
        'dark-text': '#E2E8F0',
        'dark-text-secondary': '#94A3B8',
      },
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
    },
  },
  plugins: [],
}