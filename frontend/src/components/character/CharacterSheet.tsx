import { component$, useStyles$ } from '@builder.io/qwik';
import type { CharacterStats } from '~/types/game';

interface CharacterSheetProps {
  stats: CharacterStats;
}

export const CharacterSheet = component$<CharacterSheetProps>(({ stats }) => {
  useStyles$(`
    .character-sheet {
      padding: var(--spacing-lg);
    }

    .section-title {
      font-family: var(--font-secondary);
      font-size: 1.25rem;
      color: var(--color-ink);
      margin-bottom: var(--spacing-lg);
      text-align: center;
      position: relative;
    }

    .section-title::after {
      content: '';
      position: absolute;
      bottom: -8px;
      left: 50%;
      transform: translateX(-50%);
      width: 40px;
      height: 2px;
      background: var(--color-ink);
      opacity: 0.2;
    }

    .stats-group {
      margin-bottom: var(--spacing-xl);
    }

    .stats-group:last-child {
      margin-bottom: 0;
    }

    .stat-list {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
    }

    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--spacing-sm);
      transition: transform 0.2s ease;
    }

    .stat-item:hover {
      transform: translateX(4px);
    }

    .stat-name {
      font-family: var(--font-primary);
      color: var(--color-ink-light);
      font-size: 0.95rem;
    }

    .stat-value {
      font-family: var(--font-secondary);
      color: var(--color-ink);
      font-size: 1.1rem;
      min-width: 40px;
      text-align: center;
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: 8px;
      background: var(--color-paper);
      box-shadow: var(--shadow-inset);
    }

    .inventory-list {
      display: flex;
      flex-wrap: wrap;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
    }

    .inventory-item {
      font-family: var(--font-primary);
      font-size: 0.9rem;
      color: var(--color-ink-light);
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: 6px;
      background: var(--color-paper);
      box-shadow: var(--shadow-inset);
    }

    @media (max-width: 768px) {
      .character-sheet {
        padding: var(--spacing-md);
      }

      .section-title {
        font-size: 1.1rem;
        margin-bottom: var(--spacing-md);
      }

      .stat-name {
        font-size: 0.9rem;
      }

      .stat-value {
        font-size: 1rem;
      }
    }
  `);

  return (
    <div class="character-sheet neu-flat">
      <div class="stats-group">
        <h3 class="section-title">Caractéristiques</h3>
        <div class="stat-list">
          {Object.entries(stats.Caractéristiques).map(([name, value]) => (
            <div key={name} class="stat-item">
              <span class="stat-name">{name}</span>
              <span class="stat-value">{value}</span>
            </div>
          ))}
        </div>
      </div>

      <div class="stats-group">
        <h3 class="section-title">Ressources</h3>
        <div class="stat-list">
          {Object.entries(stats.Ressources).map(([name, value]) => (
            <div key={name} class="stat-item">
              <span class="stat-name">{name}</span>
              <span class="stat-value">{value}</span>
            </div>
          ))}
        </div>
      </div>

      <div class="stats-group">
        <h3 class="section-title">Inventaire</h3>
        <div class="inventory-list">
          {stats.Inventaire.Objets.map((item, index) => (
            <span key={index} class="inventory-item">
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
});
