import { afterEach, vi } from 'vitest';
import { cleanup, render as vitestRender } from 'vitest-browser-vue';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

// Mock ResizeObserver and window
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

//create a vuetify instance for components to import from and use
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
  },
});

//provide a render that uses vuetify
export async function render(component: any, options: Record<string, any> = {}) {
  return vitestRender(component, {
    global: {
      plugins: [vuetify],
      ...(options.global || {}),
    },
    ...options,
  });
}

export { cleanup };