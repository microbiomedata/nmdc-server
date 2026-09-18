import { screen } from '@testing-library/vue';
import { expect } from 'vitest';
import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import type { StudySearchResult } from '@/data/api';
import TeamInfo from './TeamInfo.vue';

test('renders every principal investigator and merges them with credit associations', () => {
  const item = {
    principal_investigators: [
      {
        name: 'Roberto Clemente',
        orcid: 'orcid:0000-0000-0000-0001',
        profile_image_url: '/0001.jpg',
      },
      {
        name: 'Ichiro Suzuki',
        orcid: 'orcid:0000-0000-0000-0002',
        profile_image_url: '/0002.jpg',
      },
    ],
    has_credit_associations: [
      {
        applies_to_agent: { name: 'Roberto Clemente', orcid: 'orcid:0000-0000-0000-0001' },
        applied_roles: ['Project Manager', 'Principal Investigator'],
      },
      {
        applies_to_agent: { name: 'Honus Wagner', orcid: 'orcid:0000-0000-0000-0003' },
        applied_roles: ['Data Manager'],
      },
    ],
  } as unknown as StudySearchResult;

  render(TeamInfo, { props: { item } });

  expect(screen.getByText('Roberto Clemente')).toBeInTheDocument();
  expect(screen.getByText('Ichiro Suzuki')).toBeInTheDocument();
  expect(screen.getByText('Honus Wagner')).toBeInTheDocument();
  expect(screen.getAllByText(/Principal Investigator/)).toHaveLength(2);
  expect(screen.getByAltText('Roberto Clemente')).toHaveAttribute('src', '/0001.jpg');
  expect(screen.getByAltText('Ichiro Suzuki')).toHaveAttribute('src', '/0002.jpg');
});
