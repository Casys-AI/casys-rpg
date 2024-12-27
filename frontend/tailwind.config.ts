import containerQueries from '@tailwindcss/container-queries';
import forms from '@tailwindcss/forms';
import typography from '@tailwindcss/typography';
import type { Config } from 'tailwindcss';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],

  theme: {
    extend: {
      colors: {
        'game': {
          primary: '#2D3436', // Ink color
          secondary: '#636E72', // Lighter ink
          accent: '#0A3D62', // Deep blue ink
          background: '#F5F6FA', // Paper color
          surface: '#FFFFFF', // Pure white
          error: '#B33771', // Red ink
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      },
      boxShadow: {
        'neu-flat': '5px 5px 10px #d1d1d1, -5px -5px 10px #ffffff',
        'neu-pressed': 'inset 5px 5px 10px #d1d1d1, inset -5px -5px 10px #ffffff',
        'neu-border': '0 0 0 2px #e0e0e0',
      }
    }
  },

  plugins: [typography, forms, containerQueries]
} satisfies Config;
