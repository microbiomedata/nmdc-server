export type DataHarmonizerRow = Record<string, string | number | string[]>

export type DataHarmonizerData = DataHarmonizerRow[]

export type ValidationIssue = {
  row: number,
  slot: string,
  message: string,
}

const PLATE_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
const PLATE_COLS = Array.from({ length: 12 }, (_, i) => (i + 1).toString());
const VALID_WELL_ORDER = PLATE_COLS.map((col) => PLATE_ROWS.map((row) => `${row}${col}`)).flat();
const CORNER_WELLS = ['A1', 'A12', 'H1', 'H12'];
const CONT_WELL_SLOT = 'cont_well';

function getTrimmedString(value: string | number | string[] | undefined) {
  return typeof value === 'string' ? value.trim() : '';
}

export function validatePlateWellsForJgi(data: DataHarmonizerData): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const validWellSet = new Set(VALID_WELL_ORDER);
  const fillableWellOrder = VALID_WELL_ORDER.filter((well) => !CORNER_WELLS.includes(well));
  const fillableWellIndex = new Map(fillableWellOrder.map((well, index) => [well, index]));
  const duplicateWellRows = new Map<string, number[]>();
  const rowsByContainer = new Map<string, { rowIndex: number, contWell: string }[]>();

  data.forEach((row, rowIndex) => {
    const contType = getTrimmedString(row.cont_type);
    if (contType !== 'plate') {
      return;
    }

    const contWell = getTrimmedString(row.cont_well);
    if (!contWell) {
      return;
    }

    const containerName = getTrimmedString(row.container_name);

    if (!validWellSet.has(contWell)) {
      issues.push({ row: rowIndex, slot: CONT_WELL_SLOT, message: 'Invalid well ID' });
    }

    if (CORNER_WELLS.includes(contWell)) {
      issues.push({ row: rowIndex, slot: CONT_WELL_SLOT, message: 'Corner wells are not allowed' });
    }

    const duplicateKey = `${containerName}::${contWell}`;
    const duplicateRows = duplicateWellRows.get(duplicateKey) || [];
    duplicateRows.push(rowIndex);
    duplicateWellRows.set(duplicateKey, duplicateRows);

    if (!fillableWellIndex.has(contWell)) {
      return;
    }

    const containerRows = rowsByContainer.get(containerName) || [];
    containerRows.push({ rowIndex, contWell });
    rowsByContainer.set(containerName, containerRows);
  });

  duplicateWellRows.forEach((rowIndexes) => {
    if (rowIndexes.length < 2) {
      return;
    }
    rowIndexes.forEach((rowIndex) => {
      issues.push({ row: rowIndex, slot: CONT_WELL_SLOT, message: 'Well IDs must be unique on a given plate' });
    });
  });

  rowsByContainer.forEach((containerRows) => {
    if (containerRows.length === 0) {
      return;
    }

    const sortedRows = [...containerRows].sort(
      (a, b) => fillableWellIndex.get(a.contWell)! - fillableWellIndex.get(b.contWell)!,
    );
    const uniqueSortedRows = sortedRows.filter(
      (row, index) => index === 0 || row.contWell !== sortedRows[index - 1]?.contWell,
    );

    const firstRow = uniqueSortedRows[0];
    if (!firstRow) {
      return;
    }

    if (firstRow.contWell !== 'B1') {
      issues.push({
        row: firstRow.rowIndex,
        slot: CONT_WELL_SLOT,
        message: 'Plates must be filled starting with well B1',
      });
    }

    for (let i = 1; i < uniqueSortedRows.length; i += 1) {
      const previousRow = uniqueSortedRows[i - 1];
      const currentRow = uniqueSortedRows[i];
      if (!previousRow || !currentRow) {
        continue;
      }
      const previousIndex = fillableWellIndex.get(previousRow.contWell)!;
      const currentIndex = fillableWellIndex.get(currentRow.contWell)!;

      if (currentIndex !== previousIndex + 1) {
        issues.push({
          row: previousRow.rowIndex,
          slot: CONT_WELL_SLOT,
          message: 'Plates must be filled in column order. Subsequent well is not filled',
        });
      }
    }
  });

  return issues;
}
