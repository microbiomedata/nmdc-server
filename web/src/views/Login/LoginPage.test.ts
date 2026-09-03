import { defineComponent } from 'vue';
import { VApp } from 'vuetify/components';
import { useRouter } from 'vue-router';
import { render } from '@/test/setup';
import { test } from '@/test/test-extend';
import { expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/vue';
import LoginPage from './LoginPage.vue';

const { mockExchangeAuthCode, mockInit } = vi.hoisted(() => ({
  mockExchangeAuthCode: vi.fn(),
  mockInit: vi.fn(),
}));

const mockPush = vi.fn();
let mockQuery: Record<string, unknown> = {};
let mockRouter: any = { push: mockPush, currentRoute: { value: { query: mockQuery } } };

vi.mock('vue-router', async (importOriginal) => {
  const actual = (await importOriginal()) as any;
  return {
    ...actual,
    useRouter: vi.fn(() => mockRouter),
  };
});

vi.mock('@/data/api', async (importOriginal) => {
  const actual = (await importOriginal()) as any;
  return {
    ...actual,
    api: { ...actual.api, exchangeAuthCode: mockExchangeAuthCode },
  };
});

vi.mock('@/store', async (importOriginal) => {
  const actual = (await importOriginal()) as any;
  return {
    ...actual,
    init: mockInit,
  };
});

// LoginPage requires a v-app layout provider
const LoginPageInApp = defineComponent({
  components: { VApp, LoginPage },
  template: '<v-app><login-page /></v-app>',
});

beforeEach(() => {
  vi.clearAllMocks();
  mockQuery = {};
  mockRouter = { push: mockPush, currentRoute: { value: { query: mockQuery } } };
});

test.describe('LoginPage.vue', () => {
  test('Shows an error when there is no router', async () => {
    vi.mocked(useRouter).mockReturnValueOnce(undefined as any);

    render(LoginPageInApp);

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
    });
    expect(mockExchangeAuthCode).not.toHaveBeenCalled();
  });

  test('Shows an error when there is no code in the query string', async () => {
    render(LoginPageInApp);

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
    });
    expect(mockExchangeAuthCode).not.toHaveBeenCalled();
  });

  test('Shows an error when exchanging the code fails', async () => {
    mockQuery.code = 'auth-code';
    mockExchangeAuthCode.mockRejectedValueOnce(new Error('exchange failed'));

    render(LoginPageInApp);

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
    });
    expect(mockExchangeAuthCode).toHaveBeenCalledWith('auth-code');
    expect(mockInit).not.toHaveBeenCalled();
  });

  test('Exchanges the code and initializes the app when the code is valid', async () => {
    mockQuery.code = 'auth-code';
    mockQuery.state = 'submission';
    mockExchangeAuthCode.mockResolvedValueOnce(undefined);
    mockInit.mockResolvedValueOnce(undefined);

    render(LoginPageInApp);

    await waitFor(() => {
      expect(mockInit).toHaveBeenCalledWith(mockRouter, true, 'submission');
    });
    expect(mockExchangeAuthCode).toHaveBeenCalledWith('auth-code');
    expect(screen.getByText(/Logging in/)).toBeInTheDocument();
  });
});
