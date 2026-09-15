import { defineComponent } from 'vue';
import { VApp } from 'vuetify/components';
import { render, server } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { screen, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import { setConditions } from '@/store';
import SearchSidebar from './SearchSidebar.vue';
import type { Condition } from '@/data/api';

// SearchSidebar requires a v-app layout provider
const SearchSidebarInApp = defineComponent({
  components: { VApp, SearchSidebar },
  template: '<v-app><search-sidebar /></v-app>',
});

beforeEach(() => {
  vi.clearAllMocks();
  setConditions([]);
  server.use(
    http.get('/api/summary', () => HttpResponse.json({})),
  );
});

test.describe('SearchSidebar.vue', () => {
  test('Renders the search input', () => {
    render(SearchSidebarInApp);

    expect(screen.getByRole('textbox', { name: 'Search' })).toBeInTheDocument();
    expect(screen.getByText('Metadata Quality')).toBeInTheDocument();
  });

  test('Opens the Metadata Quality filter in the Sample group', async () => {
    render(SearchSidebarInApp);

    const user = userEvent.setup();
    await user.click(screen.getByText('Metadata Quality'));

    expect(await screen.findByRole('columnheader', { name: 'Badge' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Biogeochemistry Any' })).toBeChecked();
  });

  test('Does not show active query terms when there are no conditions', () => {
    render(SearchSidebarInApp);

    expect(screen.queryByText('Active query terms')).not.toBeInTheDocument();
  });

  test('Shows active query terms when conditions are present', async () => {
    setConditions([
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' } as Condition,
    ]);

    render(SearchSidebarInApp);

    await waitFor(() => {
      expect(screen.getByText('Active query terms')).toBeInTheDocument();
    });
  });

  test('Shows readable metadata badge conditions', async () => {
    setConditions([
      { table: 'biosample', field: 'badges', op: 'lacks', value: 'host_information' },
    ]);

    render(SearchSidebarInApp);

    expect((await screen.findAllByText('Metadata Quality')).length).toBeGreaterThan(0);
    expect(screen.getByText('[does not have]')).toBeInTheDocument();
    expect(screen.getByText('Host Information')).toBeInTheDocument();
  });

  test('Clears all conditions when "Clear all" is clicked', async () => {
    setConditions([
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' } as Condition,
    ]);

    render(SearchSidebarInApp);

    const user = userEvent.setup();
    await waitFor(() => {
      expect(screen.getByText('Clear all')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Clear all'));

    await waitFor(() => {
      expect(screen.queryByText('Active query terms')).not.toBeInTheDocument();
    });
  });
});
