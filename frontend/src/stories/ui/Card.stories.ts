import type { Meta, StoryObj } from '@storybook/svelte';
import Card from '$lib/components/ui/Card.svelte';

const meta = {
  title: 'UI/Card',
  component: Card,
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg']
    },
    hover: {
      control: 'boolean'
    },
    animated: {
      control: 'boolean'
    }
  }
} satisfies Meta<Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Small: Story = {
  args: {
    size: 'sm',
    hover: true
  },
  render: (args) => ({
    Component: Card,
    props: args,
    slots: {
      default: 'Small Card Content'
    }
  })
};

export const Medium: Story = {
  args: {
    size: 'md',
    hover: true
  },
  render: (args) => ({
    Component: Card,
    props: args,
    slots: {
      default: 'Medium Card Content'
    }
  })
};

export const Large: Story = {
  args: {
    size: 'lg',
    hover: true,
    animated: true
  },
  render: (args) => ({
    Component: Card,
    props: args,
    slots: {
      default: 'Large Animated Card Content'
    }
  })
};
