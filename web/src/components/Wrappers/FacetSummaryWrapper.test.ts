import { h, nextTick } from 'vue';
import { render } from '@/test/setup';
import { screen, waitFor } from '@testing-library/vue';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import type { Condition, FacetSummaryResponse } from '@/data/api';
import FacetSummaryWrapper from './FacetSummaryWrapper.vue';

const apiMocks = vi.hoisted(() => ({
  getFacetSummary: vi.fn(),
}));

vi.mock('@/data/api', () => ({ api: apiMocks }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

describe('FacetSummaryWrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('does not replace the current facet counts with an older response', async () => {
    const oldResponse = deferred<FacetSummaryResponse[]>();
    const filteredResponse = deferred<FacetSummaryResponse[]>();
    apiMocks.getFacetSummary.mockImplementation(
      (_table: string, _field: string, conditions: Condition[]) => {
        if (conditions.length === 0) {
          return Promise.resolve([{ facet: 'Metagenome', count: 4272 }]);
        }
        return conditions[0]?.value === 'first' ? oldResponse.promise : filteredResponse.promise;
      },
    );

    const condition = (value: string): Condition[] => [{
      field: 'id', op: 'like', table: 'biosample', value,
    }];
    const { rerender } = render(FacetSummaryWrapper, {
      props: {
        table: 'omics_processing', field: 'omics_type', conditions: condition('first'),
      },
      slots: {
        default: ({ facetSummary }: { facetSummary: FacetSummaryResponse[] | null }) => h(
          'div',
          { 'data-testid': 'facet-count' },
          facetSummary?.[0]?.count ?? 'loading',
        ),
      },
    });

    await rerender({ conditions: condition('filtered') });
    filteredResponse.resolve([{ facet: 'Metagenome', count: 1 }]);
    await waitFor(() => {
      expect(screen.getByTestId('facet-count')).toHaveTextContent('1');
    });
    oldResponse.resolve([{ facet: 'Metagenome', count: 4272 }]);
    await nextTick();

    expect(screen.getByTestId('facet-count')).toHaveTextContent('1');
  });
});
