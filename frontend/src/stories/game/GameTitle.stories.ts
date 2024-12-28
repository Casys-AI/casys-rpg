import type { Meta, StoryObj } from '@storybook/svelte';
import GameTitle from '$lib/components/game/GameTitle.svelte';

const meta = {
  title: 'Game/GameTitle',
  component: GameTitle,
  tags: ['autodocs']
} satisfies Meta<GameTitle>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {}
};
