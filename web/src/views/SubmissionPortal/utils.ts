import moment from 'moment';

export function formatShippingDate (date: string | Date | null | undefined): string {
  if(!date) {
    return '';
  }
  return moment(date).format('YYYY-MM-DD');
}

export function validateOrcid(orcid: string): string | boolean {
  const orcidRegex = /^(\d{4}-){3}\d{3}(\d|X)$/;
  return orcidRegex.test(orcid) || 'ORCID iD must be in valid format (0000-0000-0000-0000)';
}