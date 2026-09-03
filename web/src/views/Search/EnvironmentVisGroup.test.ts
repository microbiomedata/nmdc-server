import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect } from 'vitest';
import { screen } from '@testing-library/vue';
import { createStubs } from '@/test/stubs';
import EnvironmentVisGroup from './EnvironmentVisGroup.vue';
import type { Condition } from '@/data/api';

test.describe('EnvironmentVisGroup.vue', () => {
  const renderEnvironmentVisGroup = (props = {}) => render(EnvironmentVisGroup, {
    props: { conditions: [], ...props },
    global: {
      stubs: createStubs(),
    },
  });

  test('Renders without errors', () => {
    renderEnvironmentVisGroup();

    expect(screen.getByText('Sankey')).toBeInTheDocument();
  });

  test('Renders with inputted conditions prop', () => {
    const conditions: Condition[] = [
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' },
    ];

    renderEnvironmentVisGroup({ conditions });

    expect(screen.getByText('Sankey')).toBeInTheDocument();
  });

  test('Passes conditions to the sankey diagram', () => {
    const conditions: Condition[] = [
      { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' },
    ];

    const { container } = render(EnvironmentVisGroup, {
      props: { conditions },
      global: {
        stubs: createStubs({
          EcosystemSankey: {
            template: '<div class="sankey-stub" :data-test="JSON.stringify(conditions)">Sankey</div>',
            props: ['conditions'],
          },
        }),
      },
    });

    const sankeyElement = container.querySelector('.sankey-stub');
    expect(sankeyElement).toBeInTheDocument();
    expect(sankeyElement?.getAttribute('data-test')).toBe(JSON.stringify(conditions));
  });

  test('Handles successive condition updates', async () => {
    const { rerender } = renderEnvironmentVisGroup();

    expect(screen.getByText('Sankey')).toBeInTheDocument();

    await rerender({
      props: {
        conditions: [
          { table: 'biosample', field: 'env_medium', op: '==', value: 'soil' },
        ],
      },
    });

    expect(screen.getByText('Sankey')).toBeInTheDocument();
  });
});
