import { describe, expect, it } from 'vitest';

import {
  validatePlateWellsForJgi,
  validateReadUrlsOrInsdcRunIdentifiers,
} from './validation';

describe('validatePlateWellsForJgi', () => {
  it('returns no issues for sequential non-corner wells starting at B1', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'B1' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'C1' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'D1' },
    ]);

    expect(issues).toEqual([]);
  });

  it('flags rows with cont_type "plate" and no well ID', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: '' },
      { cont_type: 'plate', container_name: 'plate-1' },
    ]);

    expect(issues).toEqual([
      { row: 0, slot: 'cont_well', message: 'Plate position is required if container type is "plate"' },
      { row: 1, slot: 'cont_well', message: 'Plate position is required if container type is "plate"' },
    ]);
  });

  it('flags rows with a well ID and cont_type other than "plate"', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'tube', container_name: 'tube-1', cont_well: 'B1' },
      { cont_type: 'tube', container_name: 'tube-2', cont_well: 'C1' },
      { cont_type: 'tube', container_name: 'tube-3', cont_well: 'Z99' },
    ]);

    expect(issues).toEqual([
      { row: 0, slot: 'cont_well', message: 'Well ID should only be provided if container type is "plate"' },
      { row: 1, slot: 'cont_well', message: 'Well ID should only be provided if container type is "plate"' },
      { row: 2, slot: 'cont_well', message: 'Well ID should only be provided if container type is "plate"' },
    ]);
  });

  it('flags invalid well IDs', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'Z99' },
    ]);

    expect(issues).toEqual([
      { row: 0, slot: 'cont_well', message: 'Invalid well ID' },
    ]);
  });

  it('flags corner wells', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'A1' },
    ]);

    expect(issues).toEqual([
      { row: 0, slot: 'cont_well', message: 'Corner wells are not allowed' },
    ]);
  });

  it('flags duplicate wells on the same plate for both rows', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'B1' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'B1' },
      { cont_type: 'plate', container_name: 'plate-2', cont_well: 'B1' },
    ]);

    expect(issues).toEqual([
      { row: 0, slot: 'cont_well', message: 'Well IDs must be unique on a given plate' },
      { row: 1, slot: 'cont_well', message: 'Well IDs must be unique on a given plate' },
    ]);
  });

  it('flags a plate whose first populated well is not B1', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'C1' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'D1' },
    ]);

    expect(issues).toEqual([
      { row: 0, slot: 'cont_well', message: 'Plates must be filled starting with well B1' },
    ]);
  });

  it('flags the last good row when there is a gap in fill order', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'B1' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'D1' },
    ]);

    expect(issues).toEqual([
      {
        row: 0,
        slot: 'cont_well',
        message: 'Plates must be filled in column order. Subsequent well is not filled',
      },
    ]);
  });

  it('ignores non-plate rows', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'tube', container_name: 'tube-2', cont_well: '' },
      { cont_type: 'tube', container_name: 'tube-3' },
    ]);

    expect(issues).toEqual([]);
  });

  it('can return multiple issues for the same row', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'A1' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'A1' },
    ]);

    expect(issues).toEqual([
      { row: 0, slot: 'cont_well', message: 'Corner wells are not allowed' },
      { row: 1, slot: 'cont_well', message: 'Corner wells are not allowed' },
      { row: 0, slot: 'cont_well', message: 'Well IDs must be unique on a given plate' },
      { row: 1, slot: 'cont_well', message: 'Well IDs must be unique on a given plate' },
    ]);
  });
});

describe('validateReadUrlsOrInsdcRunIdentifiers', () => {
  const requiredMessage = 'This field is required unless an INSDC run identifier is provided';
  const pairedReadSlots = ['read_1_url', 'read_2_url'];
  const interleavedReadSlots = ['interleaved_url'];

  it('returns no issues when all configured paired read URLs are provided', () => {
    const issues = validateReadUrlsOrInsdcRunIdentifiers([
      {
        read_1_url: 'https://example.org/read-1.fastq.gz',
        read_2_url: 'https://example.org/read-2.fastq.gz',
      },
    ], pairedReadSlots);

    expect(issues).toEqual([]);
  });

  it('returns no issues for configured paired read slots when an INSDC run identifier is provided', () => {
    const issues = validateReadUrlsOrInsdcRunIdentifiers([
      { insdc_run_identifiers: 'SRR123456' },
    ], pairedReadSlots);

    expect(issues).toEqual([]);
  });

  it('flags whitespace-only configured slots in slot-list order on the correct row', () => {
    const issues = validateReadUrlsOrInsdcRunIdentifiers([
      { insdc_run_identifiers: 'SRR123456' },
      {
        read_1_url: ' ',
        read_2_url: '\t',
        insdc_run_identifiers: ' ',
      },
    ], ['read_2_url', 'read_1_url']);

    expect(issues).toEqual([
      { row: 1, slot: 'read_2_url', message: requiredMessage },
      { row: 1, slot: 'read_1_url', message: requiredMessage },
    ]);
  });

  it.each([
    {
      missingSlot: 'read_1_url',
      row: {
        read_2_url: 'https://example.org/read-2.fastq.gz',
        interleaved_url: 'https://example.org/interleaved.fastq.gz',
      } as Record<string, string>,
    },
    {
      missingSlot: 'read_2_url',
      row: {
        read_1_url: 'https://example.org/read-1.fastq.gz',
        interleaved_url: 'https://example.org/interleaved.fastq.gz',
      } as Record<string, string>,
    },
  ])('flags a missing $missingSlot when no INSDC run identifier is provided', ({ missingSlot, row }) => {
    const issues = validateReadUrlsOrInsdcRunIdentifiers([row], pairedReadSlots);

    expect(issues).toEqual([
      { row: 0, slot: missingSlot, message: requiredMessage },
    ]);
  });

  it('ignores unconfigured paired read slots for interleaved reads', () => {
    const issues = validateReadUrlsOrInsdcRunIdentifiers([
      { interleaved_url: 'https://example.org/interleaved.fastq.gz' },
    ], interleavedReadSlots);

    expect(issues).toEqual([]);
  });

  it('flags a missing configured interleaved read URL', () => {
    const issues = validateReadUrlsOrInsdcRunIdentifiers([
      {
        read_1_url: 'https://example.org/read-1.fastq.gz',
        read_2_url: 'https://example.org/read-2.fastq.gz',
      },
    ], interleavedReadSlots);

    expect(issues).toEqual([
      { row: 0, slot: 'interleaved_url', message: requiredMessage },
    ]);
  });
});
