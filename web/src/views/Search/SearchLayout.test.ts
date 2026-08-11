import { defineComponent, h } from 'vue';
import { VApp } from 'vuetify/components';
import { createMemoryHistory, createRouter, RouterView } from 'vue-router';
import { render, server } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { screen, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import { createStubs } from '@/test/stubs';
import { setConditions } from '@/store';
import SearchLayout from './SearchLayout.vue';
import type { StudySearchResult } from '@/data/api';

const mockStudy: StudySearchResult = {
  id: 'study-1',
  name: 'Test Study',
  description: 'Test study description',
  alternate_identifiers: [],
  annotations: { title: 'Test Study Title' },
  children: [],
  omics_processing_counts: null,
} as unknown as StudySearchResult;
// We don't need all the study fields for testing, so we cast unknown to SSR to avoid having to fill in all the required fields.

const mockStudySearchResponse = {
  count: 1,
  results: [mockStudy],
};

// BiosampleSearchResults renders individual biosample identifiers that aren't
// part of this test's mock data, so it's stubbed out; it's covered by its own tests.
const componentStubs = {
  BiosampleSearchResults: { template: '<div>Search Results</div>' },
};

beforeEach(() => {
  vi.clearAllMocks();
  setConditions([]);
  server.use(
    http.get('/api/summary', () => HttpResponse.json({})),
    http.get('/api/settings', () => HttpResponse.json({
      portal_banner_title: null,
      portal_banner_message: null,
      disable_bulk_data_product_download: false,
      disable_individual_data_product_download: false,
    })),
    http.post('/api/study/search', () => HttpResponse.json(mockStudySearchResponse)),
    http.post('/api/data_generation/facet', () => HttpResponse.json([
      { facet: '1', count: 5 },
      { facet: '2', count: 3 },
    ])),
    http.post('/api/data_object/workflow_summary', () => HttpResponse.json({})),
    http.post('/api/bulk_download/summary', () => HttpResponse.json({ count: 0, size: 0 })),
  );
});

// SearchLayout requires a v-app layout provider
// And a router to render router-links
async function renderSearchLayout() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'Search', component: SearchLayout },
      { path: '/details/study/:id', name: 'Study', component: { template: '<div />' } },
    ],
  });
  router.push('/');
  await router.isReady();

  const SearchLayoutInApp = defineComponent({
    setup: () => () => h(VApp, null, { default: () => h(RouterView) }),
  });

  return render(SearchLayoutInApp, {
    global: {
      plugins: [router],
      stubs: { ...createStubs(), ...componentStubs, RouterLink: false },
    },
  });
}

test.describe('SearchLayout.vue', () => {
  test('Renders the sample count once results load', async () => {
    await renderSearchLayout();

    await waitFor(() => {
      expect(screen.getByText(/Found 13 samples/)).toBeInTheDocument();
    });
  });

  test('Renders the search sidebar and help menu', async () => {
    await renderSearchLayout();

    expect(screen.getByRole('textbox', { name: 'Search' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Need help?' })).toBeInTheDocument();
  });

  test('Shows the Data Types & Map tab content by default', async () => {
    await renderSearchLayout();

    await waitFor(() => {
      expect(screen.getByText('Chart')).toBeInTheDocument();
    });
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('Shows the timeline visualization after switching tabs', async () => {
    await renderSearchLayout();
    const user = userEvent.setup();

    await user.click(screen.getByText('Timeline & Multi-omics'));

    await waitFor(() => {
      expect(screen.getByText('MG: Metagenomics')).toBeInTheDocument();
    });
  });

  test('Shows the environment visualization after switching tabs', async () => {
    await renderSearchLayout();
    const user = userEvent.setup();

    await user.click(screen.getByText('Environment'));

    await waitFor(() => {
      expect(screen.getByText('Sankey')).toBeInTheDocument();
    });
  });

  test('Displays study results in the studies tab by default', async () => {
    await renderSearchLayout();

    await waitFor(() => {
      expect(screen.getByText('Test Study Title')).toBeInTheDocument();
    });
  });

  test('Switches to the samples results tab', async () => {
    await renderSearchLayout();
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByText(/Samples \(13\)/)).toBeInTheDocument();
    });
    await user.click(screen.getByText(/Samples \(13\)/));

    await waitFor(() => {
      expect(screen.getByText('Search Results')).toBeInTheDocument();
    });
  });
});

