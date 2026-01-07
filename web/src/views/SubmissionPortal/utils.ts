// @ts-ignore
import moment from 'moment';

export function formatShippingDate (date: string | Date | null | undefined): string {
  if(!date) {
    return '';
  }
  return moment(date).format('YYYY-MM-DD');
}