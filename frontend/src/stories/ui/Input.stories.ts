import type { Meta, StoryObj } from '@storybook/svelte';
import Input from '$lib/components/ui/Input.svelte';

const meta = {
  title: 'UI/Input',
  component: Input,
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: { type: 'select' },
      options: ['text', 'password', 'email', 'number']
    },
    placeholder: { control: 'text' },
    value: { control: 'text' },
    disabled: { control: 'boolean' }
  }
} satisfies Meta<Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Text: Story = {
  args: {
    type: 'text',
    placeholder: 'Enter text...',
    label: 'Text Input'
  }
};

export const Password: Story = {
  args: {
    type: 'password',
    placeholder: 'Enter password...',
    label: 'Password'
  }
};

export const Disabled: Story = {
  args: {
    type: 'text',
    placeholder: 'Disabled input',
    disabled: true,
    label: 'Disabled'
  }
};
