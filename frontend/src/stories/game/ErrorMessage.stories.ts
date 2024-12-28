import type { Meta, StoryObj } from '@storybook/svelte';
import ErrorMessage from '$lib/components/game/ErrorMessage.svelte';

const meta = {
  title: 'Game/ErrorMessage',
  component: ErrorMessage,
  tags: ['autodocs'],
  argTypes: {
    message: { control: 'text' }
  }
} satisfies Meta<ErrorMessage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    message: 'An error occurred in the game engine.'
  }
};

export const NetworkError: Story = {
  args: {
    message: 'Failed to connect to the game server. Please check your connection.'
  }
};
