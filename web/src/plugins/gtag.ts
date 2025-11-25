import { createGtag } from "vue-gtag";

export default createGtag({
  tagId: import.meta.env.VITE_APP_NMDC_GOOGLE_ANALYTICS_ID || "",
})