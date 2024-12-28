import type { Meta, StoryObj } from '@storybook/svelte';
import Icon from '$lib/components/ui/Icon.svelte';

const meta = {
  title: 'UI/Icon',
  component: Icon,
  tags: ['autodocs'],
  argTypes: {
    path: { control: 'text' },
    size: { control: 'text' },
    color: { control: 'color' }
  }
} satisfies Meta<Icon>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    path: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z',
    size: '24px',
    color: 'currentColor'
  }
};
