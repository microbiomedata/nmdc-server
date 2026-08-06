import { test as testBase } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

export const test = testBase.extend({
  pinia: [
    async ({}, use) => {
      // Create a fresh pinia instance for each test
      const pinia = createPinia();
      setActivePinia(pinia);
      
      await use(pinia);
      
      // Cleanup after test
      setActivePinia(undefined as any);
    },
    {
      auto: true,
    },
  ],
});