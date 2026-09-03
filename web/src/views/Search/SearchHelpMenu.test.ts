import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect } from 'vitest';
import { screen, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import SearchHelpMenu from './SearchHelpMenu.vue';

test.describe('SearchHelpMenu.vue', () => {
  test('Renders the "Need help?" activator button', () => {
    render(SearchHelpMenu);

    expect(screen.getByRole('button', { name: 'Need help?' })).toBeInTheDocument();
  });

  test('Opens the menu and shows help links on hover', async () => {
    render(SearchHelpMenu);

    const user = userEvent.setup();
    await user.hover(screen.getByRole('button', { name: 'Need help?' }));

    await waitFor(() => {
      expect(screen.getByText('User Guide')).toBeInTheDocument();
    });
    expect(screen.getByText('NMDC Docs')).toBeInTheDocument();
    expect(screen.getByText('Video Tutorial')).toBeInTheDocument();
  });

  test('Links point to the expected documentation URLs', async () => {
    render(SearchHelpMenu);

    const user = userEvent.setup();
    await user.hover(screen.getByRole('button', { name: 'Need help?' }));

    await waitFor(() => {
      expect(screen.getByText('User Guide').closest('a')).toHaveAttribute(
        'href',
        'https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/portal_guide.html',
      );
    });
    expect(screen.getByText('NMDC Docs').closest('a')).toHaveAttribute(
      'href',
      'https://nmdc-documentation.readthedocs.io/en/latest/index.html',
    );
    expect(screen.getByText('Video Tutorial').closest('a')).toHaveAttribute(
      'href',
      'https://nmdc-documentation.readthedocs.io/en/latest/tutorials/nav_data_portal.html',
    );
  });
});
