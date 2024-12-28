import type { Meta, StoryObj } from '@storybook/svelte';
import Hero from '$lib/components/layout/Hero.svelte';

const meta = {
  title: 'Layout/Hero',
  component: Hero,
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    subtitle: { control: 'text' }
  }
} satisfies Meta<Hero>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: 'Welcome to CASYS RPG',
    subtitle: 'Embark on an AI-powered adventure'
  }
};
