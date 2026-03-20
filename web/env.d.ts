/// <reference types="vite/client" />
/// <reference types="unplugin-vue-router/client" />

interface Window {
  /** An object, populated at run time, containing Sentry configuration information */
  __nmdc_config__?: {
    /** Sentry DSN (obtained from Sentry dashboard). If empty or absent, Sentry will be disabled. */
    sentryDsn?: string;
    /** Name of Sentry environment (e.g. "production", "development", "local", "unknown"). */
    sentryEnvironmentName?: string;
    /** Probability that a given transaction will be sent to Sentry (a number from 0.0 to 1.0). */
    sentryTracesSampleRate?: number;
  };
}
