import { defineComponent } from 'vue';
import { VApp } from 'vuetify/components';
import { render, server } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { screen, waitFor } from '@testing-library/vue';
import SamplePage from './SamplePage.vue';
import type { BiosampleSearchResult } from '@/data/api';

// SamplePage requires a v-app layout provider
const SamplePageInApp = defineComponent({
  components: { VApp, SamplePage },
  props: { id: { type: String, required: true } },
  template: '<v-app><sample-page :id="id" /></v-app>',
});

const mockBiosample: BiosampleSearchResult = {
  id: 'biosamp-1',
  name: 'Test Biosample',
  description: 'Test biosample description',
  alternate_identifiers: [],
  annotations: {
    title: 'Test Biosample Title',
    depth: null,
  },
  study_id: 'study-1',
  omics_processing_id: 'omics-1',
  depth: 10,
  env_broad_scale_id: 'ENVO:00000446',
  env_local_scale_id: 'ENVO:00000447',
  env_medium_id: 'ENVO:00000448',
  longitude: -122.4,
  latitude: 37.8,
  add_date: '2026-01-01',
  mod_date: '2026-01-15',
  open_in_gold: '',
  env_broad_scale: { id: 'ENVO:00000446', label: 'Broad Scale', data: '' },
  env_local_scale: { id: 'ENVO:00000447', label: 'Local Scale', data: '' },
  env_medium: { id: 'ENVO:00000448', label: 'Medium', data: '' },
  omics_processing: [],
  emsl_biosample_identifiers: [],
} as unknown as BiosampleSearchResult;
// We don't need all the biosample fields for testing, so we cast unknown to BSR to avoid having to fill in all the required fields.

beforeEach(() => {
  vi.clearAllMocks();
  server.use(
    http.get('/api/biosample/biosamp-1', () => {
      return HttpResponse.json(mockBiosample);
    })
  );
});

test.describe('SamplePage.vue', () => {
  const renderSamplePage = (props = {}) => render(SamplePageInApp, {
    props: { id: 'biosamp-1', ...props },
  });

  test('displays loading state initially', () => {
    renderSamplePage();

    expect(screen.getByRole('alert', { name: 'Loading...' })).toBeInTheDocument();
  });

  test('Renders biosample details and related sections', async () => {
    renderSamplePage();

    await waitFor(() => {
      expect(screen.getByText('Test Biosample Title')).toBeInTheDocument();
    });
    expect(screen.getByText('Test biosample description')).toBeInTheDocument();
    expect(screen.getByText('Attributes')).toBeInTheDocument();
    expect(screen.getByText(/Download Sample Metadata/i)).toBeInTheDocument();
  });

  test('Does not display a related biosamples section when there are none', async () => {
    renderSamplePage();

    await waitFor(() => {
      expect(screen.getByText('Test Biosample Title')).toBeInTheDocument();
    });
    expect(screen.queryByText('Related Biosamples')).not.toBeInTheDocument();
  });

  test('Displays related biosamples derived from omics processing inputs', async () => {
    // Uses a different id so the axios GET cache doesn't return an earlier test's response.
    // TODO: Figure out how to clear the axios cache between tests so we can reuse mocks
    server.use(
      http.get('/api/biosample/bs-3', () => HttpResponse.json({
        ...mockBiosample,
        id: 'bs-3',
        omics_processing: [
          {
            id: 'omics-1',
            biosample_inputs: [
              { id: 'bs-2', name: 'Related Biosample' },
            ],
          },
        ],
      }))
    );

    renderSamplePage({ id: 'bs-3' });

    await waitFor(() => {
      expect(screen.getByText('Related Biosample')).toBeInTheDocument();
    });
  });
});
