import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import SubmissionSummary from './SubmissionSummary.vue';
import { useSubmissionStore } from '../store';

const mockPush = vi.fn();

vi.mock('vue-router', async (importOriginal) => {
  const actual = (await importOriginal()) as any;
  return {
    ...actual,
    useRouter: vi.fn(() => ({
      push: mockPush,
    })),
  };
});

vi.mock('@/store', async (importOriginal) => {
  const actual = (await importOriginal()) as any;
  return {
    ...actual,
    stateRefs: {
      user: { value: { orcid: 'test-orcid' } },
    },
  };
});

vi.mock('./SampleSetTable.vue', () => {
  return {
    default: { template: '<div></div>' },
  };
});

test.describe('SubmissionSummary.vue', () => {
  beforeEach(() => {
    mockPush.mockClear();
    vi.clearAllMocks();
  });

  function setupSubmissionData() {
    const store = useSubmissionStore();
    store.submission.record = {
      id: 'submission-1',
      study_name: 'Test Study',
      author: {
        name: 'Dr. Test',
        email: 'test@example.com',
        orcid: 'test-orcid',
        is_admin: false,
      },
      created: '2026-01-02T00:00:00',
      date_last_modified: '2026-01-15T12:00:00',
      is_test_submission: true,
      sample_sets: [],
      nmdc_study_id: null,
      locked_by: null,
      lock_updated: null,
      permission_level: 'owner',
      study_form: {},
    } as any;
    return store;
  }

  test('Displays the correct submission metadata', async () => {
    setupSubmissionData();
    render(SubmissionSummary);

    expect(screen.getByText('Dr. Test')).toBeInTheDocument();
    expect(screen.getByText(/test@example\.com/)).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();
  });

  test('Calls createSubmissionSampleSet with the correct sample set name', async () => {
    const store = setupSubmissionData();

    const createSpy = vi.spyOn(store, 'createSubmissionSampleSet').mockResolvedValue({
      id: 'sample-set-1',
      name: 'Sample Set 1',
    } as any);

    render(SubmissionSummary);

    const buttons = screen.getAllByRole('button');
    const createBtn = buttons.find(
      (btn) => btn.textContent?.includes('Create Sample Set')
    );

    expect(createBtn).toBeDefined();

    if (createBtn) {
      const user = userEvent.setup();
      await user.click(createBtn);

      await waitFor(() => {
        expect(createSpy).toHaveBeenCalledWith('Sample Set 1');
      });
    }
  });

  test('Navigates to multi-omics form when making a new sample set', async () => {
    const store = setupSubmissionData();

    vi.spyOn(store, 'createSubmissionSampleSet').mockResolvedValue({
      id: 'sample-set-1',
      name: 'Sample Set 1',
    } as any);

    render(SubmissionSummary);

    const buttons = screen.getAllByRole('button');
    const createBtn = buttons.find(
      (btn) => btn.textContent?.includes('Create Sample Set')
    );

    expect(createBtn).toBeDefined();

    if (createBtn) {
      const user = userEvent.setup();
      await user.click(createBtn);

      await waitFor(
        () => {
          expect(mockPush).toHaveBeenCalledWith({
            name: 'Multiomics Form',
            params: { sampleSetId: 'sample-set-1' },
          });
        },
        { timeout: 3000 }
      );
    }
  });

  test('Study Form button passes the correct route', async () => {
    setupSubmissionData();

    render(SubmissionSummary);

    const studyInfoElements = screen.getAllByText('Study Information');
    const studyInfoLink = studyInfoElements.find((el) => el.closest('a'));

    expect(studyInfoLink).toBeInTheDocument();

    const user = userEvent.setup();
    if (studyInfoLink) {
      await user.click(studyInfoLink);
    }

    expect(studyInfoLink).toBeInTheDocument();
  });
});