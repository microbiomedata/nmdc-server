import { render, server } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { screen } from '@testing-library/vue';
import { createStubs } from '@/test/stubs';
import DataTypesVisGroup from './DataTypesVisGroup.vue';
import type { Condition, FacetSummaryResponse } from '@/data/api';

const mockFacetSummary: FacetSummaryResponse[] = [
  { facet: 'metagenomics', count: 100 },
  { facet: 'metatranscriptomics', count: 75 },
  { facet: 'metabolomics', count: 50 },
];

beforeEach(() => {
  vi.clearAllMocks();
  // Set default handlers for all tests
  server.use(
    http.post('/api/biosample/facet', () => {
      return HttpResponse.json(mockFacetSummary);
    }),
    http.post('/api/study/facet', () => {
      return HttpResponse.json(mockFacetSummary);
    })
  );
});

test.describe('DataTypesVisGroup.vue', () => {
  const renderDataTypesVisGroup = (props = {}, customStubs = {}) => render(DataTypesVisGroup, {
    props: { conditions: [], ...props },
    global: {
      stubs: createStubs(customStubs),
    },
  });

  test('Renders without errors', () => {
    renderDataTypesVisGroup({ activeVisTab: 'overview' });

    // Verify both main sections render
    expect(screen.getByText('Chart')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('Displays both chart and map sections', () => {
    renderDataTypesVisGroup({ activeVisTab: null });

    expect(screen.getByText('Chart')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('Renders with inputted conditions prop', () => {
    const conditions: Condition[] = [
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' },
    ];

    renderDataTypesVisGroup({ conditions, activeVisTab: 'overview' });

    expect(screen.getByText('Chart')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('Renders with multiple conditions', () => {
    const conditions: Condition[] = [
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' },
      { table: 'biosample', field: 'depth', op: '>', value: '1000' },
    ];

    renderDataTypesVisGroup({ conditions, activeVisTab: 'map' });

    expect(screen.getByText('Chart')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('Renders with different activeVisTab values', () => {
    const tabs = ['overview', 'map', 'timeline', null];

    for (const tab of tabs) {
      const { unmount } = renderDataTypesVisGroup({ activeVisTab: tab });

      expect(screen.getByText('Chart')).toBeInTheDocument();
      expect(screen.getByText('Map')).toBeInTheDocument();
      unmount();
    }
  });

  test('Passes conditions to child components', () => {
    const conditions: Condition[] = [
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' },
    ];

    const { container } = renderDataTypesVisGroup({ conditions }, {
      ClusterMap: {
        template: '<div class="map-stub" :data-test="JSON.stringify(conditions)">Map</div>',
        props: ['conditions'],
      },
    });

    const mapElement = container.querySelector('.map-stub');
    expect(mapElement).toBeInTheDocument();
  });

  test('Passes activeVisTab to ClusterMap', () => {
    const { container } = renderDataTypesVisGroup({ activeVisTab: 'map' }, {
      ClusterMap: {
        template: '<div class="map-stub" :data-tab="activeVisTab">Map</div>',
        props: ['activeVisTab'],
      },
    });

    const mapElement = container.querySelector('[data-tab="map"]');
    expect(mapElement).toBeInTheDocument();
  });

  test('Handles empty facet summary data', () => {
    server.use(
      http.post('/api/biosample/facet', () => {
        return HttpResponse.json([]);
      }),
      http.post('/api/study/facet', () => {
        return HttpResponse.json([]);
      })
    );

    renderDataTypesVisGroup();

    expect(screen.getByText('Chart')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('Renders layout structure', () => {
    const { container } = renderDataTypesVisGroup();

    // Verify layout divs exist
    const mainDiv = container.querySelector('div');
    expect(mainDiv).toBeInTheDocument();

    // Verify both sections are rendered
    expect(screen.getByText('Chart')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('Handles successive condition updates', async () => {
    const { rerender } = renderDataTypesVisGroup();

    expect(screen.getByText('Chart')).toBeInTheDocument();

    const newConditions: Condition[] = [
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' },
    ];

    await rerender({
      props: { conditions: newConditions },
    });

    expect(screen.getByText('Chart')).toBeInTheDocument();

    const anotherCondition: Condition[] = [
      { table: 'biosample', field: 'depth', op: '>', value: '1000' },
    ];

    await rerender({
      props: { conditions: anotherCondition },
    });

    expect(screen.getByText('Chart')).toBeInTheDocument();
  });

  test('Component accepts all expected props', () => {
    const conditions: Condition[] = [
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' },
    ];

    renderDataTypesVisGroup({ conditions, activeVisTab: 'map' });

    // If component renders without error, props were accepted correctly
    expect(screen.getByText('Chart')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('Renders successfully with no activeVisTab', () => {
    renderDataTypesVisGroup({ activeVisTab: null });

    expect(screen.getByText('Chart')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });
});