import type { Meta, StoryObj } from '@storybook/svelte';
import LoadingSpinner from '$lib/components/game/LoadingSpinner.svelte';

const meta = {
  title: 'Game/LoadingSpinner',
  component: LoadingSpinner,
  tags: ['autodocs'],
  argTypes: {
    size: { control: 'text' },
    color: { control: 'color' }
  }
} satisfies Meta<LoadingSpinner>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    size: '48px',
    color: '#4d7cff'
  }
};

export const Small: Story = {
  args: {
    size: '24px',
    color: '#4d7cff'
  }
};

export const Large: Story = {
  args: {
    size: '96px',
    color: '#4d7cff'
  }
};
