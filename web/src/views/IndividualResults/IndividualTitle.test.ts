import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect } from 'vitest';
import { screen } from '@testing-library/vue';
import IndividualTitle from './IndividualTitle.vue';
import type { BaseSearchResult } from '@/data/api';

//Mock item to be displayed.
const mockItem: BaseSearchResult = {
  id: 'item-1',
  name: 'Mocked Item Name',
  description: 'Mocked Item description',
  alternate_identifiers: [],
  annotations: {
    title: 'Mocked Item Title',
  },
};

test.describe('IndividualTitle.vue', () => {
  test('Displays the annotation title when present', () => {
    render(IndividualTitle, {
      props: { item: mockItem },
    });

    expect(screen.getByText('Mocked Item Title')).toBeInTheDocument();
  });

  test('Uses item name when no annotation title is present', () => {
    render(IndividualTitle, {
      props: {
        item: { ...mockItem, annotations: {} },
      },
    });

    expect(screen.getByText('Mocked Item Name')).toBeInTheDocument();
  });

  test('Displays the description as the subtitle by default', () => {
    render(IndividualTitle, {
      props: { item: mockItem },
    });

    expect(screen.getByText('Mocked Item description')).toBeInTheDocument();
  });

  test('Displays a different field as the subtitle when subtitleKey is set', () => {
    render(IndividualTitle, {
      props: {
        item: { ...mockItem, id: 'custom-id' },
        subtitleKey: 'id',
      },
    });

    expect(screen.getByText('custom-id')).toBeInTheDocument();
    expect(screen.queryByText('Mocked Item description')).not.toBeInTheDocument();
  });

  test('Does not render a subtitle when the subtitle field is empty', () => {
    render(IndividualTitle, {
      props: {
        item: { ...mockItem, description: '' },
      },
    });

    expect(screen.getByText('Mocked Item Title')).toBeInTheDocument();
    expect(screen.queryByText('Mocked Item description')).not.toBeInTheDocument();
  });

  test('Renders slot content instead of the subtitle field when provided', () => {
    render(IndividualTitle, {
      props: { item: mockItem },
      slots: {
        subtitle: '<div>Custom subtitle content</div>',
      },
    });

    expect(screen.getByText('Custom subtitle content')).toBeInTheDocument();
    expect(screen.queryByText('Mocked Item description')).not.toBeInTheDocument();
  });
});
