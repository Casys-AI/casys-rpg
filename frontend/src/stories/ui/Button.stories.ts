import type { Meta, StoryObj } from '@storybook/svelte';
import Button from '$lib/components/ui/Button.svelte';

const meta = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary']
    }
  }
} satisfies Meta<Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button'
  }
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button'
  }
};

export const Loading: Story = {
  args: {
    loading: true,
    children: 'Loading Button'
  }
};

export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Disabled Button'
  }
};
