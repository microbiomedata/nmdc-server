import { getCurrentInstance } from 'vue';

/**
 * Custom hook to access Google Analytics gtag instance.
 * returns $gtag instance if available, otherwise undefined.
 * In development, this will return undefined.
 * Note that this must be used within the setup() function of a component.
 */
export default function useGtag() {
  const instance = getCurrentInstance();
  const gtag = instance?.proxy?.$gtag;
  return gtag;
}
