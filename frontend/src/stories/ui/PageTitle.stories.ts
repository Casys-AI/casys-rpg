import type { Meta, StoryObj } from '@storybook/svelte';
import PageTitle from '$lib/components/ui/PageTitle.svelte';

const meta = {
  title: 'UI/PageTitle',
  component: PageTitle,
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    subtitle: { control: 'text' }
  }
} satisfies Meta<PageTitle>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: 'Welcome to CASYS RPG',
    subtitle: 'An AI-powered role-playing game'
  }
};

export const WithoutSubtitle: Story = {
  args: {
    title: 'Welcome to CASYS RPG'
  }
};
