// Components that wrap third-party libraries incompatible with jsdom (Google Charts,
// Leaflet) can't render naturally in tests and must always be stubbed.
export const externalLibraryStubs = {
  FacetBarChart: { template: '<div class="chart-stub">Chart</div>' },
  ClusterMap: { template: '<div class="map-stub">Map</div>' },
  EcosystemSankey: { template: '<div class="sankey-stub">Sankey</div>' },
};

// Helper to merge the required external-library stubs with test-specific overrides.
// Prefer letting everything else render naturally with the real `render()` helper.
export function createStubs(overrides: Record<string, any> = {}) {
  return {
    ...externalLibraryStubs,
    ...overrides,
  };
}