import { getCurrentInstance } from '@vue/composition-api';

/**
 * Custom hook to access Google Analytics gtag instance.
 * returns $gtag instance if available, otherwise undefined.
 * In development, this will return undefined.
 */
export default function useGtag() {
  const instance = getCurrentInstance();
  const gtag = instance?.proxy?.$gtag;
  return gtag;
}
