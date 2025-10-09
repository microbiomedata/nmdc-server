import LinkifyIt from 'linkify-it';
import { Condition } from './api';

function removeCondition(conditions: Condition[], conds: Condition[]) {
  const copy = conditions.slice();
  conds.forEach((c) => {
    const foundIndex = copy.findIndex((cond) => (
      cond.table === c.table
      && cond.field === c.field
      && cond.op === c.op
      && cond.value === c.value));
    if (foundIndex >= 0) {
      copy.splice(foundIndex, 1);
    }
  });
  return copy;
}

/**
 * Format bytes as human-readable text.
 *
 * @param bytes Number of bytes.
 * @param si True to use metric (SI) units, aka powers of 1000. False to use
 *           binary (IEC), aka powers of 1024.
 * @param dp Number of decimal places to display.
 *
 * @return Formatted string.
 *
 * https://stackoverflow.com/questions/10420352/converting-file-size-in-bytes-to-human-readable-string
 */
function humanFileSize(bytes: number | null, si = false, dp = 1) {
  if (!bytes) {
    return '';
  }

  const thresh = si ? 1000 : 1024;
  if (Math.abs(bytes) < thresh) {
    return `${bytes} B`;
  }
  const units = si
    ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
  let u = -1;
  const r = 10 ** dp;
  let _bytes = bytes;
  do {
    _bytes /= thresh;
    u += 1;
  } while (Math.round(Math.abs(_bytes) * r) / r >= thresh && u < units.length - 1);

  return `${_bytes.toFixed(dp)} ${units[u]}`;
}

/**
 * from https://stackoverflow.com/questions/6234773/can-i-escape-html-special-chars-in-javascript
 */
export function escapeHtml(unsafe: string) {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/'/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function urlify(text: string): string {
  const matcher = new LinkifyIt();
  if (!text) {
    return '';
  }

  const matches = matcher.match(text);
  if (!matches) {
    return text;
  }

  let urlified = '';
  let lastIndex = 0;
  matches.forEach((match) => {
    if (match.index > lastIndex) {
      urlified += text.substring(lastIndex, match.index);
    }
    urlified += `<a href="${match.url}" target="_blank" rel="noopener noreferrer">${match.text}</a>`;
    lastIndex = match.lastIndex;
  });
  return urlified;
}

export {
  humanFileSize,
  removeCondition,
};
