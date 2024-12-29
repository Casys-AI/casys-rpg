import containerQueries from '@tailwindcss/container-queries';
import forms from '@tailwindcss/forms';
import typography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}', './.storybook/**/*.{html,js,svelte,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'game': {
          background: {
            light: '#ffffff',
            dark: '#1a1a1a',
            DEFAULT: '#ffffff'
          },
          primary: {
            light: '#1a1a1a',
            dark: '#e2e8f0',
            DEFAULT: '#1a1a1a'
          },
          secondary: {
            light: '#4b5563',
            dark: '#94a3b8',
            DEFAULT: '#4b5563'
          },
          accent: {
            light: '#4d7cff',
            dark: '#4d7cff',
            DEFAULT: '#4d7cff'
          },
          toggle: {
            dark: '#171717',
            darker: '#090909',
            light: '#444245',
            border: '#7d7c7e',
            icon: '#a5a5a5'
          },
          card: {
            light: '#e0e0e0',
            dark: '#212121',
            DEFAULT: '#e0e0e0'
          },
          error: '#B33771'
        }
      },
      backgroundImage: {
        'toggle-gradient': 'linear-gradient(145deg, #171717, #444245)',
        'toggle-outer': 'linear-gradient(145deg, #262626, #606060)',
        'styled-gradient': 'linear-gradient(to bottom, #171717, #242424)',
        'styled-border': 'linear-gradient(to bottom, #292929, #000000)'
      },
      boxShadow: {
        'neu-light-flat': '6px 6px 12px rgb(190 190 190), -6px -6px 12px rgb(255 255 255)',
        'neu-dark-flat': '6px 6px 12px rgb(26 26 26), -6px -6px 12px rgb(61 61 61)',
        'neu-light-pressed': 'inset 4px 4px 12px rgb(190 190 190), inset -4px -4px 12px rgb(255 255 255)',
        'neu-dark-pressed': 'inset 4px 4px 12px rgb(26 26 26), inset -4px -4px 12px rgb(61 61 61)',
        'neu-light-card': '20px 20px 60px rgb(190 190 190), -20px -20px 60px rgb(255 255 255)',
        'neu-dark-card': '20px 20px 60px rgb(26 26 26), -20px -20px 60px rgb(61 61 61)',
        'toggle': '5px 5px 10px #151515, -5px -5px 10px #1f1f1f',
        'toggle-outer': '5px 5px 10px #151515, -5px -5px 10px #1f1f1f',
        'toggle-checked': '0 0 15px #4d7cff',
        'card-light': '15px 15px 30px #bebebe, -15px -15px 30px #ffffff',
        'card-dark': '15px 15px 30px #1c1c1c, -15px -15px 30px #262626'
      },
      dropShadow: {
        'styled': '0 10px 20px rgb(26 25 25 / 0.9) 0 0 4px rgb(0 0 0)',
        'styled-hover': '0 10px 20px rgb(50 50 50) 0 0 20px rgb(2 2 2)'
      },
      keyframes: {
        'pulse': {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' }
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' }
        },
        'fadeIn': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        'slideIn': {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        },
        'fill': {
          '0%': { transform: 'scale(0)' },
          '50%': { transform: 'scale(1.2)' },
          '100%': { transform: 'scale(1)' }
        },
        'border': {
          '0%': { borderColor: 'rgba(77, 124, 255, 0)' },
          '100%': { borderColor: 'rgba(77, 124, 255, 0.3)' }
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'fill': 'fill 0.5s ease forwards',
        'border': 'border 0.5s ease forwards'
      }
    }
  },
  plugins: [
    forms,
    typography,
    containerQueries
  ]
}
