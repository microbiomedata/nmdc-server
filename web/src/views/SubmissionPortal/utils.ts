import moment, { invalid } from 'moment';
import { read, utils, xlsxUtils } from 'xlsx';
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';
import { Contributor } from '@/views/SubmissionPortal/types.ts';

export function formatShippingDate (date: string | Date | null | undefined): string {
  if(!date) {
    return '';
  }
  return moment(date).format('YYYY-MM-DD');
}

export function checkDoiFormat(v: string): string | boolean {
  return /^(?:doi:)?10.\d{2,9}\/.*$/.test(v) || 'DOI must be in the format "10.xxxx/xxxxx"';
}

const ORCID_REGEX = /^(\d{4}-){3}\d{3}(\d|X)$/;

export function validateOrcid(orcid: string): string | boolean {
  if (!orcid) {
    return true;
  }
  // const orcidRegex = /^(\d{4}-){3}\d{3}(\d|X)$/;
  // return orcidRegex.test(orcid) || 'ORCID iD must be in valid format (0000-0000-0000-0000)';
  return ORCID_REGEX.test(orcid) || 'ORCID iD must be in valid format (0000-0000-0000-0000)';
}

const CREDIT_ROLES = Object.keys(NmdcSchema.enums.CreditEnum.permissible_values);
const CREDIT_ROLE_LOOKUP = new Map(CREDIT_ROLES.map((role) => [role.toLowerCase(), role]));

const NAME_COLUMNS = ['name', 'full name', 'contributor name'];
const ORCID_COLUMNS = ['orcid', 'orcid id', 'orcid ida'];
const CREDIT_ROLE_COLUMNS = ['credit', 'credit roles', 'roles'];

export interface ContributorImportError {
  row: number;
  message: string;
}

export interface ContributorImportResult {
  contributors: Contributor[];
  errors: ContributorImportError[];
}

function findColumnValue(row: Record<string, unknown>, candidates: string[]): string {
  const key = Object.keys(row).find((k) => candidates.includes(k.trim().toLowerCase()));
  const value = key ? row[key] : undefined;
  return value === undefined || value === null ? '' : String(value).trim();
}

function normalizeOrcid(raw: string): string { 
  return raw.trim().replace(/^orcid:/i, '');
}

// Splits CRediT roles cell into role names, matching case-insentitively against the NMDC 
// schema's CreditEnum. Tokens that don't match a permissible value are returned 'invalid'.
export function parseContributorRoles(raw: string): { roles: string[]; invalid: string[] } {
  const roles: string[] = [];
  const invalid: string[] = [];
  raw.split(/[,;]/).map((r) => r.trim()).filter(Boolean).forEach((token) => {
    const canonical = CREDIT_ROLE_LOOKUP.get(token.toLowerCase());
    if (canonical) {
      if (!roles.includes(canonical)) {
        roles.push(canonical);
      }
    } else {
      invalid.push(token);
    }
  });
  return { roles, invalid };
}

// Parses an uploaded spreadsheet of contributors into validated Contributor objects. 
// Expects columns for Name, ORCID, and CRediT roles. Rows that fail are skipped and
// reported in 'errors' rather than failing the whole import. 
export async function parseContributorsSpreadsheet(file: File): Promise<ContributorImportResult> {
  const buffer = await file.arrayBuffer();
  const workbook = read(buffer);
  const firstSheetName = workbook.SheetNames[0];
  const worksheet = firstSheetName ? workbook.Sheets[firstSheetName] : undefined;
  const rows: Record<string, unknown>[] = worksheet ? xlsxUtils.sheet_to_json(worksheet) : [];
  const contributors: Contributor[] = [];
  const errors: ContributorImportError[] = [];
  const seenOrcids = new Set<string>();

  rows.forEach((row, i) => {
    const rowNumber = i + 2; // +2 to account for header row and 0-based index
    const name = findColumnValue(row, NAME_COLUMNS);
    const orcidRaw = findColumnValue(row, ORCID_COLUMNS);
    const creditRaw = findColumnValue(row, CREDIT_COLUMNS);

    if (!name && !orcidRaw && !creditRaw) {
      // Skip empty rows
      return;
    }

    if (!name) {
      errors.push({ row: rowNumber, message: 'Missing contributor name' });
      return;
    }

    const orcid = normalizeOrcid(orcidRaw);
    if (!orcid || !ORCID_REGEX.test(orcid)) {
      errors.push({
        row: rowNumber,
        message: `Invalid ORCID iD "${orcidRaw}". Expected format: 0000-0000-0000-0000`,
      });
      return;
    }

    if (seenOrcids.has(orcid)) {
      errors.push({
        row: rowNumber,
        message: `Duplicate ORCID iD "${orcid}" found in the spreadsheet`,
      });
      return;
    }

    const {roles, invalid} = parseContributorRoles(creditRaw);
    if (invalid.length > 0) {
      errors.push({
        row: rowNumber,
        message: `Invalid CRediT roles: ${invalid.join(', ')}`,
      });
      return;
    }
    if (roles.length === 0) {
      errors.push({
        row: rowNumber,
        message: 'At least one CRediT role is required for each contributor',
      });
      return;
    }

    seenOrcids.add(orcid);
    contributors.push({
      name,
      orcid,
      roles,
      permissionLevel: null
    });
  });
  
  return { contributors, errors };
}