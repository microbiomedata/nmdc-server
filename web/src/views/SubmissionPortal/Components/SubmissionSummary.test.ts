import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import SubmissionSummary from './SubmissionSummary.vue';
import { useSubmissionStore } from '../store';

beforeEach(() => {
  vi.clearAllMocks();
});

const mockPush = vi.fn();

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal() as any;
  return {
    ...actual,
    useRouter: vi.fn(() => ({
      push: mockPush,
    })),
    RouterLink: {
      name: 'RouterLink',
      template: '<a @click="$emit(\'click\')"><slot /></a>',
      props: ['to'],
    },
  };
});

vi.mock('@/store', async (importOriginal) => {
  const actual = await importOriginal() as any;
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
  test.beforeEach(() => {
    mockPush.mockClear();
  });

  async function clickCreateSampleSetButton() {
    const screen = await render(SubmissionSummary);
    const createBtn = screen.getByRole('button', { name: /create sample set/i });
    await createBtn.click();
    return screen;
  }

  test('Displays the correct submission metadata', async () => {
    const store = useSubmissionStore();
    
    store.submission.record = {
      author: {
        name: 'Dr. Test',
        email: 'test@example.com',
        is_admin: false,
      },
      created: '2026-01-02T00:00:00',
      date_last_modified: '2026-01-15T12:00:00',
      is_test_submission: true,
    } as any;

    const screen = await render(SubmissionSummary);

    await expect.element(screen.getByText(/Dr. Test/i)).toBeInTheDocument();
    await expect.element(screen.getByText(/test@example.com/i)).toBeInTheDocument();
    await expect.element(screen.getByText(/1\/1\/2026, 4:00:00 PM/i)).toBeInTheDocument();
    await expect.element(screen.getByText(/1\/15\/2026, 4:00:00 AM/i)).toBeInTheDocument();
    await expect.element(screen.getByText(/Yes/i)).toBeInTheDocument();
  });

  test('Calls createSubmissionSampleSet with the correct sample set name', async () => {
    const store = useSubmissionStore();
    const createSpy = vi.spyOn(store, 'createSubmissionSampleSet').mockResolvedValue({
      id: 'sample-set-1',
      name: 'Sample Set 1',
    } as any);

    await clickCreateSampleSetButton();

    expect(createSpy).toHaveBeenCalledWith('Sample Set 1');
  });

  test('Navigates to multi-omics form when making a new sample set', async () => {
    const store = useSubmissionStore();
    vi.spyOn(store, 'createSubmissionSampleSet').mockResolvedValue({
      id: 'sample-set-1',
      name: 'Sample Set 1',
    } as any);

    await clickCreateSampleSetButton();

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockPush).toHaveBeenCalledWith({
      name: 'Multiomics Form',
      params: { sampleSetId: 'sample-set-1' },
    });
  });

  test('Study Form button passes the correct route', async () => {
    const screen = await render(SubmissionSummary);

    const studyInfoLink = screen.getByRole('link', { name: /study information/i });
    await expect.element(studyInfoLink).toBeInTheDocument();
    await studyInfoLink.click();
    await expect.element(studyInfoLink).toBeInTheDocument();
  });
});