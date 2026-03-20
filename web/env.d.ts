/// <reference types="vite/client" />
/// <reference types="unplugin-vue-router/client" />

interface Window {
  /**
   * Runtime configuration injected into `index.html` at container startup.
   * Values are set by replacing the `<!-- __NMDC_RUNTIME_CONFIG__ -->` placeholder
   * with a `<script>` tag that assigns this object.
   */
  __nmdc_config__?: {
    /** Sentry DSN to use for error reporting. If empty/absent, Sentry is disabled. */
    sentryDsn?: string;
    /** Name of the deployment environment (e.g. "production", "development"). */
    sentryEnvironmentName?: string;
  };
}
