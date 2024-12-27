import { $, useSignal, useOnDocument } from '@builder.io/qwik';

/**
 * Hook de gestion du thème (clair/sombre)
 */
export const useTheme = () => {
  const theme = useSignal<'light' | 'dark'>('light');

  // Fonction pour mettre à jour le thème
  const updateTheme = $((newTheme: 'light' | 'dark') => {
    theme.value = newTheme;
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', newTheme);
      document.documentElement.classList.toggle('dark', newTheme === 'dark');
    }
  });

  // Écouter les changements de préférence système
  useOnDocument('DOMContentLoaded', $(() => {
    // Récupérer le thème sauvegardé
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      
      // Utiliser le thème sauvegardé ou la préférence système
      const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
      updateTheme(initialTheme);

      // Écouter les changements de préférence système
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
          updateTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
  }));

  // Actions de changement de thème
  const actions = {
    /**
     * Basculer entre les thèmes
     */
    toggle: $(() => {
      updateTheme(theme.value === 'light' ? 'dark' : 'light');
    }),

    /**
     * Définir un thème spécifique
     */
    set: $((newTheme: 'light' | 'dark') => {
      updateTheme(newTheme);
    }),

    /**
     * Utiliser la préférence système
     */
    useSystem: $(() => {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        updateTheme(prefersDark ? 'dark' : 'light');
      }
    })
  };

  return {
    theme,
    actions
  };
};
