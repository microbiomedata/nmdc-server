import { screen } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';

import type { Condition } from '@/data/api';
import { render } from '@/test/setup';
import { snakeToSentenceCase } from '@/utils';
import FilterMetadataQuality from './FilterMetadataQuality.vue';

const badges = Object.keys(NmdcSchema.enums.MetadataBadgeEnum.permissible_values);

test('renders every schema badge with Any selected by default', () => {
  render(FilterMetadataQuality, { props: { conditions: [] } });

  badges.forEach((badge) => {
    expect(screen.getByText(snakeToSentenceCase(badge))).toBeInTheDocument();
    expect(screen.getByRole('radio', {
      // Note that `name` checks multiple values, including aria-label
      // See https://testing-library.com/docs/queries/byrole/
      name: `${snakeToSentenceCase(badge)} Any`,
    })).toBeChecked();
  });
});

test('hydrates badge conditions and emits an immediate selection', async () => {
  const [badge] = badges;
  const conditions: Condition[] = [
    { table: 'study', field: 'name', op: 'like', value: 'soil' },
    { table: 'biosample', field: 'badges', op: 'lacks', value: badge! },
  ];
  const { emitted } = render(FilterMetadataQuality, { props: { conditions } });

  expect(screen.getByRole('radio', {
    name: `${snakeToSentenceCase(badge!)} No`,
  })).toBeChecked();

  await userEvent.click(screen.getByRole('radio', {
    name: `${snakeToSentenceCase(badge!)} Yes`,
  }));

  const selections = emitted().select!;
  expect(selections[selections.length - 1]).toEqual([{
    conditions: [
      conditions[0],
      { table: 'biosample', field: 'badges', op: 'has', value: badge },
    ],
  }]);
});

test('selecting Any removes only that badge condition', async () => {
  const [badge, otherBadge] = badges;
  const conditions: Condition[] = [
    { table: 'biosample', field: 'badges', op: 'has', value: badge! },
    { table: 'biosample', field: 'badges', op: 'lacks', value: otherBadge! },
    { table: 'biosample', field: 'geo_loc_name', op: '==', value: 'USA' },
  ];
  const { emitted } = render(FilterMetadataQuality, { props: { conditions } });

  await userEvent.click(screen.getByRole('radio', {
    name: `${snakeToSentenceCase(badge!)} Any`,
  }));

  const selections = emitted().select!;
  expect(selections[selections.length - 1]).toEqual([{
    conditions: [conditions[1], conditions[2]],
  }]);
});
