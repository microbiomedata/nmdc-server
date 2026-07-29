// src/test/test-extend.ts
import { test as testBase } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { worker } from './mocks/worker';

export const test = testBase.extend({
  worker: [
    async ({}, use) => {
      setActivePinia(createPinia());
      
      // Start the worker before the test
      await worker.start();

      // Expose the worker object on the test's context
      await use(worker);

      // Reset handlers after the test
      worker.resetHandlers();
    },
    {
      auto: true,
    },
  ],
});