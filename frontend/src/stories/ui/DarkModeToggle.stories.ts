import type { Meta, StoryObj } from '@storybook/svelte';
import DarkModeToggle from '$lib/components/ui/DarkModeToggle.svelte';

const meta = {
  title: 'UI/DarkModeToggle',
  component: DarkModeToggle,
  tags: ['autodocs']
} satisfies Meta<DarkModeToggle>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {}
};
