import { describe, expect, it } from 'vitest';

import { validatePlateWellsForJgi } from './validation';

describe('validatePlateWellsForJgi', () => {
  it('returns no issues for sequential non-corner wells starting at B1', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'B1' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'C1' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: 'D1' },
    ]);

    expect(issues).toEqual([]);
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

  it('ignores non-plate rows and blank wells', () => {
    const issues = validatePlateWellsForJgi([
      { cont_type: 'tube', container_name: 'tube-1', cont_well: 'Z99' },
      { cont_type: 'plate', container_name: 'plate-1', cont_well: '' },
      { cont_type: 'plate', container_name: 'plate-1' },
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
