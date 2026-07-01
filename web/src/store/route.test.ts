import { describe, expect, it } from 'vitest';

import { routeHasConditions } from './route';

function routeWithQuery(query: Record<string, unknown>) {
  return { query } as Parameters<typeof routeHasConditions>[0];
}

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
