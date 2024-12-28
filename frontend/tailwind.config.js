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
          shadow: {
            light: {
              DEFAULT: '#ffffff',
              dark: '#bebebe'
            },
            dark: {
              DEFAULT: '#000000',
              light: '#3d3d3d'
            }
          },
          'styled': {
            dark: '#171717',
            darker: '#242424',
            border: '#292929',
            black: '#000000'
          },
          input: {
            shadow: {
              dark: 'rgb(0 0 0)',
              light: 'rgb(255 255 255 / 0.4)'
            }
          }
        }
      },
      fontFamily: {
        'serif': ['Cinzel', 'serif'],
        'sans': ['Inter', 'sans-serif']
      },
      backgroundImage: {
        'toggle-gradient': 'linear-gradient(145deg, #171717, #444245)',
        'toggle-outer': 'linear-gradient(145deg, #262626, #606060)',
        'styled-gradient': 'linear-gradient(to bottom, #171717, #242424)',
        'styled-border': 'linear-gradient(to bottom, #292929, #000000)'
      },
      dropShadow: {
        'styled': '0 10px 20px rgb(26 25 25 / 0.9) 0 0 4px rgb(0 0 0)',
        'styled-hover': '0 10px 20px rgb(50 50 50) 0 0 20px rgb(2 2 2)'
      },
      boxShadow: {
        'neu-light-flat': '6px 6px 12px rgb(190 190 190), -6px -6px 12px rgb(255 255 255)',
        'neu-dark-flat': '6px 6px 12px rgb(26 26 26), -6px -6px 12px rgb(61 61 61)',
        'neu-light-pressed': 'inset 4px 4px 12px rgb(190 190 190), inset -4px -4px 12px rgb(255 255 255)',
        'neu-dark-pressed': 'inset 4px 4px 12px rgb(26 26 26), inset -4px -4px 12px rgb(61 61 61)',
        'neu-light-card': '20px 20px 60px rgb(190 190 190), -20px -20px 60px rgb(255 255 255)',
        'neu-dark-card': '20px 20px 60px rgb(26 26 26), -20px -20px 60px rgb(61 61 61)'
      },
      keyframes: {
        'pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '.5' }
        },
        'animeFill': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(180deg)' }
        },
        'animeBorder': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' }
        },
        'label-float': {
          '0%': { transform: 'translateY(0)', opacity: '0' },
          '100%': { transform: 'translateY(-1rem)', opacity: '1' }
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fill': 'animeFill 0.3s linear alternate-reverse infinite',
        'border': 'animeBorder 0.3s linear alternate-reverse infinite',
        'label-float': 'label-float 0.3s ease forwards'
      }
    }
  },
  plugins: []
};
