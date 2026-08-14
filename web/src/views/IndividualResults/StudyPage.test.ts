import { defineComponent } from 'vue';
import { VApp } from 'vuetify/components';
import { createMemoryHistory, createRouter } from 'vue-router';
import { render, server } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { screen, waitFor, fireEvent } from '@testing-library/vue';
import StudyPage from './StudyPage.vue';
import { api } from '@/data/api';
import type { StudySearchResult } from '@/data/api';
import userEvent from '@testing-library/user-event';

const { mockDownloadJson } = vi.hoisted(() => ({
  mockDownloadJson: vi.fn(),
}));

vi.mock('@/utils', async (importOriginal) => {
  const actual = (await importOriginal()) as any;
  return {
    ...actual,
    downloadJson: mockDownloadJson,
  };
});

// StudyPage requires a v-app layout provider
const StudyPageInApp = defineComponent({
  components: { VApp, StudyPage },
  props: { id: { type: String, required: true } },
  template: '<v-app><study-page :id="id" /></v-app>',
});

// BiosampleSearchResults renders individual biosample identifiers that aren't
// part of this test's mock data, and it's covered by its own test file, so it's stubbed
const componentStubs = {
  BiosampleSearchResults: { template: '<div>Search Results</div>' },
};

const mockStudy: StudySearchResult = {
  id: 'study-123',
  name: 'Test Study',
  description: 'Test study description',
  type: 'Study',
  annotations: {
    title: 'Test Study Title',
    emsl_project_identifiers: [],
  },
  sample_count: 13,
  children: [],
  part_of: null,
  doi_map: {},
  omics_processing_counts: null,
  gold_study_identifiers: [],
  homepage_website: [],
  principal_investigator_websites: [],
  funding_sources: [],
  protocol_link: [],
  image_url: null,
  principal_investigator_image_url: '',
  principal_investigator_name: 'Dr. Test',
  principal_investigator: {
    name: 'Dr. Test',
    email: 'test@example.com',
  },
  omics_counts: [],
  award_dois: [],
  dataset_dois: [],
  publication_dois: [],
  gold_name: '',
  gold_description: '',
  scientific_objective: '',
  add_date: '2026-01-01',
  mod_date: '2026-01-15',
  open_in_gold: '',
  has_credit_associations: null,
  alternate_identifiers: [],
} as unknown as StudySearchResult;
// We don't need all the study fields for testing, so we cast unknown to SSR to avoid having to fill in all the required fields.

beforeEach(() => {
  vi.clearAllMocks();
  //This handler is used for the initial study page load to fetch the mock study data
  //It's too specific to be a general handler
  server.use(
    http.get('/api/study/study-123', () => {
      return HttpResponse.json(mockStudy);
    })
  );
});

test.describe('StudyPage.vue', () => {
  const renderStudyPage = (props = {}, customStubs = {}) => render(StudyPageInApp, {
    props: { id: 'study-123', ...props },
    global: {
      stubs: { ...componentStubs, ...customStubs },
    },
  });

  test('Renders without errors', async () => {
    renderStudyPage();

    await waitFor(() => {
      expect(screen.getByText('Test study description')).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/All Samples: 13/)).toBeInTheDocument();
    });
  });

  test('Displays study information', async () => {
    renderStudyPage();

    await waitFor(() => {
      expect(screen.getByText('Test Study Title')).toBeInTheDocument();
      expect(screen.getByText('Test study description')).toBeInTheDocument();
      expect(screen.getByText(/All Samples: 13/)).toBeInTheDocument();
    });
  });

  test('Displays page sections', async () => {
    renderStudyPage();

    await waitFor(() => {
      expect(screen.getByText('Team')).toBeInTheDocument();
      expect(screen.getByText('Study Details')).toBeInTheDocument();
      expect(screen.getByText('Related External Resources')).toBeInTheDocument();
      expect(screen.getByText('Samples')).toBeInTheDocument();
    });
  });

  test('Displays loading state initially', () => {
    renderStudyPage();

    expect(screen.getByRole('alert', { name: 'Loading...' })).toBeInTheDocument();
  });

  test('Renders with child studies', async () => {
    // TODO: same as in SamplePage test, figure out how to clear axios. Or maybe it's better
    // convention to create a new mock for each test anyway
    const studyWithChildren: StudySearchResult = {
      ...mockStudy,
      id: 'study-456',
      children: [
        {
          ...mockStudy,
          id: 'child-study-1',
          name: 'Child Study',
          annotations: { ...mockStudy.annotations, title: 'Child Study' },
        } as unknown as StudySearchResult,
      ],
    };

    server.use(
      http.get('/api/study/study-456', () => {
        return HttpResponse.json(studyWithChildren);
      })
    );

    // Need to use a real router to get router-links to render
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'Search', component: { template: '<div />' } },
        { path: '/details/study/:id', name: 'Study', component: { template: '<div />' } },
      ],
    });
    router.push('/');
    await router.isReady();

    render(StudyPageInApp, {
      props: { id: 'study-456' },
      global: {
        plugins: [router],
        stubs: { ...componentStubs, RouterLink: false },
      },
    });

    await waitFor(() => {
      expect(screen.getByText('Test Study Title')).toBeInTheDocument();
    });
    expect(screen.getByText('Associated Studies')).toBeInTheDocument();
    expect(screen.getByText('Child Study')).toBeInTheDocument();
  });

  test('Handles study with no omics processing counts', async () => {
    renderStudyPage();

    await waitFor(() => {
      expect(screen.getByText('Test Study Title')).toBeInTheDocument();
    });
  });

  test('Calls getStudySource and downloads the file when the download is confirmed', async () => {
    const sourceData = { id: 'study-123', name: 'Test Study Source', raw: true };
    server.use(
      http.get('/api/study/study-123/source_metadata', () => HttpResponse.json(sourceData))
    );
    const getStudySourceSpy = vi.spyOn(api, 'getStudySource');

    renderStudyPage();

    const downloadBtn = await screen.findByText(/Download Study Metadata/i);
    const user = userEvent.setup();
    await user.click(downloadBtn);

    const confirmBtn = await screen.findByText(/Accept and continue to download/i);
    // FireEvent is used here because userEvent causes failure with this button setup in jsdom
    await fireEvent.click(confirmBtn.closest('button')!);

    await waitFor(() => {
      expect(mockDownloadJson).toHaveBeenCalledWith(sourceData, 'study-123.json');
    });
    expect(getStudySourceSpy).toHaveBeenCalledWith('study-123');
  });

  test('Shows an error dialog and does not download the file when the API call fails', async () => {
    //suppress console output for test, errors from this test are expected and handled
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    // Uses a different id so the axios GET cache doesn't return an earlier test's response.
    // TODO: Another axios cache fix
    server.use(
      http.get('/api/study/study-789', () => HttpResponse.json({ ...mockStudy, id: 'study-789' })),
      http.get('/api/study/study-789/source_metadata', () => HttpResponse.json(
        { detail: 'Internal Server Error' },
        { status: 500 },
      ))
    );

    renderStudyPage({ id: 'study-789' });

    const downloadBtn = await screen.findByText(/Download Study Metadata/i);
    const user = userEvent.setup();
    await user.click(downloadBtn);

    const confirmBtn = await screen.findByText(/Accept and continue to download/i);
    await fireEvent.click(confirmBtn.closest('button')!);

    await waitFor(() => {
      expect(screen.getByText('Your download could not be completed.')).toBeInTheDocument();
    });
    expect(mockDownloadJson).not.toHaveBeenCalled();
    consoleErrorSpy.mockRestore();
  });

  test('Displays team info section', async () => {
    renderStudyPage();

    await waitFor(() => {
      expect(screen.getByText('Dr. Test')).toBeInTheDocument();
      expect(screen.getByText('Principal Investigator')).toBeInTheDocument();
    });
  });
});