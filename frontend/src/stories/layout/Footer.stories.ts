import type { Meta, StoryObj } from '@storybook/svelte';
import Footer from '$lib/components/layout/Footer.svelte';

const meta = {
  title: 'Layout/Footer',
  component: Footer,
  tags: ['autodocs']
} satisfies Meta<Footer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {}
};
