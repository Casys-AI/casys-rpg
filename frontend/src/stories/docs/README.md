# Storybook Documentation

## Structure Overview

The stories are organized in the following directories:

- `ui/`: Basic UI components (buttons, inputs, cards, etc.)
- `layout/`: Layout components (headers, footers, navigation, etc.)
- `game/`: Game-specific components (character cards, inventory items, etc.)
- `pages/`: Full page stories
- `docs/`: Documentation and guidelines

## Writing Stories

### File Naming Convention
- Component stories: `ComponentName.stories.svelte`
- Documentation: `ComponentName.mdx`

### Basic Story Template
```svelte
import type { Meta, StoryObj } from '@storybook/svelte';
import ComponentName from '$lib/components/ComponentName.svelte';

const meta = {
  title: 'Category/ComponentName',
  component: ComponentName,
  tags: ['autodocs'],
} satisfies Meta<ComponentName>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    // Component props here
  }
};
```

## Best Practices
1. Always include component documentation
2. Use TailwindCSS classes consistently
3. Test components in different viewports
4. Include accessibility information
