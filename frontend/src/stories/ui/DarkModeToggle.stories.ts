import type { Meta, StoryObj } from '@storybook/svelte';
import DarkModeToggle from '$lib/components/ui/DarkModeToggle.svelte';

const meta = {
  title: 'UI/DarkModeToggle',
  component: DarkModeToggle,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#ffffff' },
        { name: 'dark', value: '#1a1a1a' }
      ]
    }
  }
} satisfies Meta<DarkModeToggle>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story par défaut
export const Default: Story = {};

export const Light: Story = {
  parameters: {
    backgrounds: { default: 'light' }
  }
};

export const Dark: Story = {
  parameters: {
    backgrounds: { default: 'dark' }
  }
};
