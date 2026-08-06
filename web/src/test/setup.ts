import { afterEach, beforeAll, vi } from 'vitest';
import { cleanup, render as testingLibraryRender } from '@testing-library/vue';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';
import '@testing-library/jest-dom/vitest';
import * as matchers from '@testing-library/jest-dom/matchers';
import { expect } from 'vitest';

// Extend Vitest's expect method with methods from react-testing-library
expect.extend(matchers);

// Mock CSS imports
vi.mock('*.css', () => ({ default: '' }));

// Setup MSW server for Node environment
const server = setupServer(...handlers);

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

// Mock ResizeObserver and window APIs
declare global {
  interface Window {
    ResizeObserver: any;
  }
}

class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

window.ResizeObserver = MockResizeObserver as any;
window.visualViewport = {
  width: 1024,
  height: 768,
  offsetLeft: 0,
  offsetTop: 0,
  pageLeft: 0,
  pageTop: 0,
  scale: 1,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
} as any;

// Create a vuetify instance for components to import from and use
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
  },
});

// Provide a render that uses vuetify
export function render(component: any, options: Record<string, any> = {}) {
  return testingLibraryRender(component, {
    global: {
      plugins: [vuetify],
      stubs: {
        RouterLink: true,
        transition: false,
        'transition-stub': false,
      },
      ...(options.global || {}),
    },
    ...options,
  });
}

export { cleanup, server };