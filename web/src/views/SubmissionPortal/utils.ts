import moment from 'moment';

export function formatShippingDate (date: string | Date | null | undefined): string {
  if(!date) {
    return '';
  }
  return moment(date).format('YYYY-MM-DD');
}

export function checkDoiFormat(v: string): string | boolean {
  return /^(?:doi:)?10.\d{2,9}\/.*$/.test(v) || 'DOI must be in the format "10.xxxx/xxxxx"';
}
