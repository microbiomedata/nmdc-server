import { beforeAll, describe, expect, it } from 'vitest';

let routeHasConditions: typeof import('./index').routeHasConditions;

function routeWithQuery(query: Record<string, unknown>) {
  return { query } as Parameters<typeof routeHasConditions>[0];
}

beforeAll(async () => {
  // The store imports the API client, which reads window.location at module load time.
  // Provide just enough browser global for this focused helper test.
  globalThis.window = {
    location: { origin: 'http://localhost' },
    localStorage: {
      getItem: () => null,
      setItem: () => undefined,
      removeItem: () => undefined,
    },
  } as unknown as Window & typeof globalThis;

  ({ routeHasConditions } = await import('./index'));
});

describe('routeHasConditions', () => {
  it('detects decoded URL conditions so startup does not overwrite pasted filters', () => {
    expect(routeHasConditions(routeWithQuery({
      conditions: [{
        table: 'study',
        field: 'principal_investigator_name',
        op: '==',
        value: 'Kate Thibault',
      }],
    }))).toBe(true);
  });

  it('treats an empty decoded conditions list as no URL filter state', () => {
    expect(routeHasConditions(routeWithQuery({ conditions: [] }))).toBe(false);
  });

  it('treats routes without conditions as restorable from saved local query state', () => {
    expect(routeHasConditions(routeWithQuery({ view: 'data-types' }))).toBe(false);
  });
});
