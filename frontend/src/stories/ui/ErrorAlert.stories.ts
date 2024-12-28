import type { Meta, StoryObj } from '@storybook/svelte';
import ErrorAlert from '$lib/components/ui/ErrorAlert.svelte';

const meta = {
  title: 'UI/ErrorAlert',
  component: ErrorAlert,
  tags: ['autodocs'],
  argTypes: {
    message: { control: 'text' }
  }
} satisfies Meta<ErrorAlert>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    message: 'An error occurred while processing your request.'
  }
};

export const LongMessage: Story = {
  args: {
    message: 'This is a very long error message that should wrap to multiple lines when the content exceeds the container width.'
  }
};
