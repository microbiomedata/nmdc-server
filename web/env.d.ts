/// <reference types="vite/client" />
/// <reference types="unplugin-vue-router/client" />

interface Window {
  /**
   * Run-time configuration injected into `index.html` at container startup.
   * Values are set by replacing the `<!-- __NMDC_CONFIG_INJECTION_PLACEHOLDER__ -->` placeholder
   * with a `<script>` tag that assigns this object.
   */
  __nmdc_config__?: {
    /** Sentry DSN to use for error reporting. If empty/absent, Sentry is disabled. */
    sentryDsn?: string;
    /** Name of the deployment environment (e.g. "production", "development"). */
    sentryEnvironmentName?: string;
    /** Fraction of transactions to sample for performance tracing (0.0–1.0). */
    sentryTracesSampleRate?: number;
  };
}
