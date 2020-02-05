import moment from 'moment';
import filesize from 'filesize';
import { types } from './encoding';

export function valueCardinality(value) {
  if (Array.isArray(value)) {
    return value.length;
  }
  return 1;
}

export function typeWithCardinality(type, cardinality) {
  if (cardinality === 1) {
    return types[type].name;
  }
  return types[type].plural;
}

export function capitalizeAcronyms(word) {
  if (['id', 'ncbi', 'gold', 'jgi'].includes(word.toLowerCase())) {
    return word.toUpperCase();
  }
  return word;
}

export function toSentenceCase(word) {
  return `${word[0].toUpperCase()}${word.slice(1)}`;
}

export function fieldDisplayName(field) {
  return field.split('_')
    .map((word, i) => (i === 0 ? toSentenceCase(word) : word))
    .map((word) => capitalizeAcronyms(word))
    .reduce((prev, cur) => `${prev}${prev === '' ? '' : ' '}${cur}`, '');
}

export function valueDisplayName(field, value) {
  if (field.includes('date')) {
    return moment.utc(value).format('YYYY-MM-DD, hh:mm:ss');
  }
  if (field === 'file_size') {
    return filesize(value);
  }
  return `${value}`;
}
