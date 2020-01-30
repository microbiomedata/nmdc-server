import moment from 'moment';

export function valueCardinality(value) {
  if (Array.isArray(value)) {
    return value.length;
  }
  return 1;
}

export function typeWithCardinality(type, cardinality) {
  if (cardinality === 1) {
    return type;
  }
  return {
    study: 'studies',
    project: 'projects',
    sample: 'samples',
    file: 'files',
  }[type];
}

export function toSentenceCase(word) {
  if (['id', 'ncbi'].includes(word)) {
    return word.toUpperCase();
  }
  return `${word[0].toUpperCase()}${word.slice(1)}`;
}

export function fieldDisplayName(field) {
  return field.split('_')
    .map((word, i) => (i === 0 ? toSentenceCase(word) : word))
    .reduce((prev, cur) => `${prev}${prev === '' ? '' : ' '}${cur}`, '');
}

export function valueDisplayName(field, value) {
  if (field.includes('date')) {
    return moment.utc(value).format('YYYY-MM-DD, hh:mm:ss');
  }
  return `${value}`;
}
