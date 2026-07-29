import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { SetupWorker } from 'msw/browser';
import TimelineVisGroup from './TimelineVisGroup.vue';

beforeEach(() => {
  vi.clearAllMocks();
});

test.describe('TimelineVisGroup.vue', () => {
  test('renders without errors', async () => {
    const screen = await render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    await expect.element(screen.getByText(/collection date/i)).toBeInTheDocument();
  });

  test('displays all UpSet legend items', async () => {
    const screen = await render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    const legends = [
      'MG: Metagenomics',
      'MP: Metaproteomics',
      'MB: Metabolomics',
      'MT: Metatranscriptomics',
    ];

    for (const legend of legends) {
      await expect.element(screen.getByText(legend)).toBeInTheDocument();
    }
  });

  test('renders with inputted props', async () => {
    const conditions = [
      { table: 'biosample' as const, field: 'env_medium', op: '==' as const, value: 'soil' },
    ];

    const screen = await render(TimelineVisGroup, {
      props: { conditions },
    });

    await expect.element(screen.getByText(/collection date/i)).toBeInTheDocument();
  });

  test('calls both biosample and study facet summary APIs', async ({ worker }: { worker: SetupWorker}) => {
    const biosampleSpy = vi.fn(() => HttpResponse.json([{ facet: '1', count: 5 }]));
    const studySpy = vi.fn(() => HttpResponse.json([{ facet: '1', count: 3 }]));

    worker.use(
      http.post('/api/biosample/facet', biosampleSpy),
      http.post('/api/study/facet', studySpy)
    );

    await render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    // Wait for API calls
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(biosampleSpy).toHaveBeenCalled();
    expect(studySpy).toHaveBeenCalled();
  });

  test('handles empty facet summary data', async ({ worker }: { worker: SetupWorker}) => {
    worker.use(
      http.post('/api/biosample/facet', () => {
        return HttpResponse.json([]);
      }),
      http.post('/api/study/facet', () => {
        return HttpResponse.json([]);
      })
    );

    const screen = await render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    // Component should still render
    await expect.element(screen.getByText(/collection date/i)).toBeInTheDocument();
  });
});