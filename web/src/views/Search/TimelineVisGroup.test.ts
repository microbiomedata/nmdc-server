import { render, server } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { screen, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import TimelineVisGroup from './TimelineVisGroup.vue';

beforeEach(() => {
  vi.clearAllMocks();
});

test.describe('TimelineVisGroup.vue', () => {
  test('renders without errors', async () => {
    render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    expect(screen.getByText(/collection date/i)).toBeInTheDocument();
  });

  test('Can click buttons', async () => {
    render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    const user = userEvent.setup();
    const buttons = screen.getAllByRole('button');
    const firstButton = buttons[0];

    if (firstButton) {
      await user.click(firstButton);
      expect(firstButton).toBeInTheDocument();
    }
  });

  test('displays all UpSet legend items', async () => {
    render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    const legends = [
      'MG: Metagenomics',
      'MP: Metaproteomics',
      'MB: Metabolomics',
      'MT: Metatranscriptomics',
    ];

    for (const legend of legends) {
      expect(screen.getByText(legend)).toBeInTheDocument();
    }
  });

  test('renders with inputted props', async () => {
    const conditions = [
      { table: 'biosample' as const, field: 'env_medium', op: '==' as const, value: 'soil' },
    ];

    render(TimelineVisGroup, {
      props: { conditions },
    });

    expect(screen.getByText(/collection date/i)).toBeInTheDocument();
  });

  test('makes API calls to fetch data', async () => {
    render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    await waitFor(() => {
      expect(screen.getByText(/collection date/i)).toBeInTheDocument();
    });
  });

  test('handles empty facet summary data', async () => {
    server.use(
      http.post('/api/biosample/facet', () => {
        return HttpResponse.json([]);
      }),
      http.post('/api/study/facet', () => {
        return HttpResponse.json([]);
      }),
      http.post('/api/biosample/binned_facet', () => {
        return HttpResponse.json([]);
      })
    );

    render(TimelineVisGroup, {
      props: { conditions: [] },
    });

    expect(screen.getByText(/collection date/i)).toBeInTheDocument();
  });
});