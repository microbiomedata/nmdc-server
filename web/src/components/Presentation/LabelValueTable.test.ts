import { screen, within } from '@testing-library/vue';
import { expect } from 'vitest';
import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import LabelValueTable from './LabelValueTable.vue';

test.describe('LabelValueTable.vue', () => {
  test('renders rows as label-value pairs', () => {
    render(LabelValueTable, {
      props: {
        rows: [
          { label: 'Study ID', value: 'nmdc:sty-1' },
          { label: 'Sample count', value: 12 },
        ],
      },
    });

    const table = screen.getByRole('table', { name: 'Label value table' });
    const rows = within(table).getAllByRole('row');

    expect(rows).toHaveLength(2);
    expect(within(rows[0]!).getByRole('rowheader')).toHaveTextContent('Study ID');
    expect(within(rows[0]!).getAllByRole('cell')[1]).toHaveTextContent('nmdc:sty-1');
    expect(within(rows[1]!).getByRole('rowheader')).toHaveTextContent('Sample count');
    expect(within(rows[1]!).getAllByRole('cell')[1]).toHaveTextContent('12');
  });
});
