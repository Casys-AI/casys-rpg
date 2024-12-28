import type { Meta, StoryObj } from '@storybook/svelte';
import Card from '$lib/components/ui/Card.svelte';

const meta = {
  title: 'UI/Card',
  component: Card,
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large']
    }
  }
} satisfies Meta<Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Small: Story = {
  args: {
    size: 'small',
    children: 'Small Card'
  }
};

export const Medium: Story = {
  args: {
    size: 'medium',
    children: 'Medium Card'
  }
};

export const Large: Story = {
  args: {
    size: 'large',
    children: 'Large Card'
  }
};
