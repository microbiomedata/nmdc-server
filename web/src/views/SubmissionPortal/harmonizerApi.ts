import {
  Ref, ref, nextTick,
} from '@vue/composition-api';
import { debounce } from 'lodash';
import { DataHarmonizer, Footer } from 'data-harmonizer';
import {
  HARMONIZER_TEMPLATES,
  EMSL,
  JGI_MG,
  JGI_MG_LR,
  JGT_MT,
  MetadataSuggestionRequest,
} from '@/views/SubmissionPortal/types';

// a simple data structure to define the relationships between the GOLD ecosystem fields
const GOLD_FIELDS = {
  ecosystem: {
    upstream: [],
    downstream: ['ecosystem_category', 'ecosystem_type', 'ecosystem_subtype', 'specific_ecosystem'],
  },
  ecosystem_category: {
    upstream: ['ecosystem'],
    downstream: ['ecosystem_type', 'ecosystem_subtype', 'specific_ecosystem'],
  },
  ecosystem_type: {
    upstream: ['ecosystem', 'ecosystem_category'],
    downstream: ['ecosystem_subtype', 'specific_ecosystem'],
  },
  ecosystem_subtype: {
    upstream: ['ecosystem', 'ecosystem_category', 'ecosystem_type'],
    downstream: ['specific_ecosystem'],
  },
  specific_ecosystem: {
    upstream: ['ecosystem', 'ecosystem_category', 'ecosystem_type', 'ecosystem_subtype'],
    downstream: [],
  },
};

export function getVariants(checkBoxes: string[], dataGenerated: boolean | undefined, base: string[]): string[] {
  const templates = new Set(base);
  if (dataGenerated) {
    return Array.from(templates);
  }
  if (checkBoxes.includes('mp-emsl') || checkBoxes.includes('mb-emsl') || checkBoxes.includes('nom-emsl')) {
    templates.add(EMSL);
  }
  if (checkBoxes.includes('mg-jgi')) {
    templates.add(JGI_MG);
  }
  if (checkBoxes.includes('mg-lr-jgi')) {
    templates.add(JGI_MG_LR);
  }
  if (checkBoxes.includes('mt-jgi')) {
    templates.add(JGT_MT);
  }
  return Array.from(templates);
}

interface CellData {
  row: number,
  col: number,
  text: string,
}

export class HarmonizerApi {
  schemaSectionNames: Ref<Record<string, string>>;

  schemaSectionColumns: Ref<Record<string, Record<string, number>>>;

  ready: Ref<boolean>;

  goldEcosystemTree: any;

  dh: any;

  footer: any;

  selectedColumn: Ref<string>;

  schema: any;

  slotNames: string[];

  slotInfo: Map<string, { columnIndex: number, title: string }>;

  constructor() {
    this.schemaSectionNames = ref({});
    this.schemaSectionColumns = ref({});
    this.ready = ref(false);
    this.selectedColumn = ref('');
    this.slotNames = [];
    this.slotInfo = new Map<string, { columnIndex: number, title: string }>();
  }

  async init(r: HTMLElement, schema: any, templateName: string | undefined, goldEcosystemTree: any) {
    this.schema = schema;
    this.goldEcosystemTree = goldEcosystemTree;

    // Attempt to find each template's underlying schema class, pull the excel_worksheet_name annotation from it
    // and add it to the template object.
    Object.values(HARMONIZER_TEMPLATES).forEach((template) => {
      if (!template.schemaClass) {
        return;
      }
      const classDefinition = schema.classes[template.schemaClass];
      if (!classDefinition) {
        return;
      }
      // eslint-disable-next-line no-param-reassign
      template.excelWorksheetName = classDefinition.annotations?.excel_worksheet_name?.value;
    });

    this.dh = new DataHarmonizer(r, {
      modalsRoot: document.querySelector('.harmonizer-style-container'),
      fieldSettings: this._getFieldSettings(),
      columnHelpEntries: ['column', 'description', 'guidance', 'examples'],
      // we use our own custom help sidebar, so turn off DataHarmonizer's built-in one
      helpSidebar: {
        enabled: false,
      },
    });
    this.footer = new Footer(document.querySelector('#harmonizer-footer-root'), this.dh);
    this.dh.useSchema(this.schema, [], templateName);
    this._postTemplateChange();

    // @ts-ignore
    window.dh = this.dh;

    this.ready.value = true;
  }

  _getColumnCoordinates() {
    const ret: Record<string, Record<string, number>> = {};
    let column_ptr = 0;
    this.dh.template.forEach((section: any) => {
      ret[section.title] = { '': column_ptr };
      section.children.forEach((column: any) => {
        ret[section.title][column.title] = column_ptr;
        column_ptr += 1;
      });
    });
    return ret;
  }

  _getSameRowCellData(columnNames: string[]): string[] {
    const row = this.dh.hot.getSelectedLast()[0];
    return columnNames.map((columnName) => {
      const col = this.dh.getFields().findIndex((field: any) => field.name === columnName);
      if (col < 0) {
        return null;
      }
      return this.dh.hot.getDataAtCell(row, col);
    });
  }

  _getGoldOptions(path: string[] = []) {
    let options: any = this.goldEcosystemTree.children;
    for (let i = 0; i < path.length; i += 1) {
      const name = path[i];
      const item = options.find((child: any) => child.name === name);
      if (!item) {
        options = [];
        break;
      }
      options = item.children;
    }
    return options.map((child: any) => child.name);
  }

  _getFieldSettings() {
    const fieldSettings: any = {};
    const fieldNames = Object.keys(GOLD_FIELDS);
    for (let i = 0; i < fieldNames.length; i += 1) {
      const field = fieldNames[i] as keyof typeof GOLD_FIELDS;
      fieldSettings[field] = {
        getColumn: (dh: any, col: {[key: string]: any}) => {
          let flatVocab: string[];
          const fieldObj = dh.getFields().find((f: any) => f.name === field);
          if (fieldObj && fieldObj.flatVocabulary) {
            flatVocab = fieldObj.flatVocabulary;
          }
          const newCol = { ...col };
          // define a dynamic source field. this function gets the 'upstream' dependent fields,
          // looks up the valid completions in the GOLD classification tree, and provides those
          // as the autocomplete options. If the field has an enum range in the schema (i.e.
          // the field object has a `flatVocabulary` field here) then the options are restricted
          // to that set.
          newCol.source = (_: any, next: (opts: any) => void) => {
            const dependentRowData = this._getSameRowCellData(GOLD_FIELDS[field].upstream);
            let options = this._getGoldOptions(dependentRowData);
            if (flatVocab) {
              options = options.filter((o: string) => flatVocab.indexOf(o) >= 0);
            }
            next(options);
          };
          newCol.type = 'autocomplete';
          newCol.trimDropdown = false;
          return newCol;
        },
        onChange: (change: any[], fields: any, triggered_changes: any[]) => {
          // clear downstream fields if the value changes
          if (change[2] !== change[3]) {
            const { downstream } = GOLD_FIELDS[field];
            for (let j = 0; j < downstream.length; j += 1) {
              const other = downstream[j];
              const otherIdx = fields.findIndex((f: any) => f.title === other);
              triggered_changes.push([change[0], otherIdx, change[2], null]);
            }
          }
        },
      };
    }
    return fieldSettings;
  }

  _postTemplateChange() {
    this.dh.hot.addHook('afterSelection', debounce((_, col: number) => {
      const column = this.dh.getFields()[col];
      if (!column) {
        this.selectedColumn.value = '';
      } else {
        this.selectedColumn.value = column.title;
      }
    }, 200, { leading: true }));
    this.dh.hot.updateSettings({
      search: true,
      customBorders: true,
      height: '100%',
      width: '100%',
      outsideClickDeselects: false,
    });
    this.jumpToRowCol(0, 0);
    this.slotInfo.clear();
    this.dh.getFields().forEach((field: any, idx: number) => {
      this.slotInfo.set(field.name, {
        columnIndex: idx,
        title: field.title || field.name,
      });
    });
    this.slotNames = [...this.slotInfo.keys()];
  }

  refreshState() {
    this.schemaSectionNames.value = this.dh.template.reduce((acc: any, section: any) => {
      acc[section.title] = section.name;
      return acc;
    }, {});
    this.schemaSectionColumns.value = this._getColumnCoordinates();
  }

  async loadData(data: any[]) {
    if (!this.ready.value) {
      return;
    }
    await this.dh.loadDataObjects(data);
    await this.dh.hot.render();
    this.refreshState();
  }

  changeVisibility(value: string) {
    switch (value) {
      case 'all':
        this.dh.showAllColumns();
        break;
      case 'required':
        this.dh.showRequiredColumns();
        break;
      case 'recommended':
        this.dh.showRecommendedColumns();
        break;
      default:
        this.dh.showColumnsBySectionTitle(value);
    }
  }

  getHelp(title: string) {
    const field = this.dh.getFields().filter((f: any) => f.title === title)[0];
    return this.dh.getCommentDict(field);
  }

  find(query: string) {
    const search = this.dh.hot.getPlugin('search');
    const results = search.query(query);
    nextTick(this.dh.hot.render);
    return results;
  }

  highlight(row?: number, col?: number) {
    const borders = this.dh.hot.getPlugin('customBorders');
    nextTick(() => borders.clearBorders());
    if (row !== undefined && col !== undefined) {
      nextTick(() => borders.setBorders([[row, col, row, col]], {
        left: { hide: false, width: 2, color: 'magenta' },
        right: { hide: false, width: 2, color: 'magenta' },
        top: { hide: false, width: 2, color: 'magenta' },
        bottom: { hide: false, width: 2, color: 'magenta' },
      }));
    }
  }

  getCellData(row: number, col: number): CellData {
    const text = this.dh.hot.getDataAtCell(row, col);
    return { row, col, text };
  }

  setCellData(data: CellData[]) {
    this.dh.hot.setDataAtCell(data.map((d) => [d.row, d.col, d.text]));
  }

  getDataByRows(rows: number[]): MetadataSuggestionRequest[] {
    const rowData: MetadataSuggestionRequest[] = [];
    rows.forEach((row) => {
      if (rowData.find((r) => r.row === row)) {
        return;
      }
      const currentRowDataArray = this.dh.hot.getDataAtRow(row);
      const currentRowData = Object.fromEntries(
        currentRowDataArray
          .map((value: string, index: number) => [this.slotNames[index], value])
          .filter(([, value]: [string, string]) => value != null && value !== ''),
      );
      rowData.push({ row, data: currentRowData });
    });
    return rowData;
  }

  exportJson() {
    return this.dh.getDataObjects(false);
  }

  scrollViewportTo(row: number, column: number) {
    this.dh.hot.scrollViewportTo(row, column);
  }

  jumpToRowCol(row: number, column: number) {
    this.dh.scrollTo(row, column);
  }

  getSelectedCells(): number[][] {
    return this.dh.hot.getSelected();
  }

  launchReference() {
    this.dh.renderReference();
  }

  setupTemplate(folder: string) {
    this.dh.setupTemplate(folder);
  }

  async validate() {
    await this.dh.validate();
    this.refreshState();
    return this.dh.invalid_cells;
  }

  addBeforeChangeHook(callback: Function) {
    if (!this.ready.value) {
      return;
    }
    // calls function on any non-programmatic change of the data
    this.dh.hot.addHook('beforeChange', (changes: any[], source: string | null) => {
      if (source === 'loadData') {
        return;
      }
      callback();
    });
  }

  addChangeHook(callback: Function) {
    if (!this.ready.value) {
      return;
    }
    // calls function on any non-programmatic change of the data
    this.dh.hot.addHook('afterChange', (changes: any[], source: string | null) => {
      if (source === 'loadData') {
        return;
      }
      callback(changes, source);
    });
  }

  useTemplate(template: string | undefined) {
    if (!this.dh || !template) {
      return;
    }
    this.dh.useTemplate(template);
    this._postTemplateChange();
  }

  setColumnsReadOnly(slotNames: string[]) {
    const { hot } = this.dh;
    const { columns } = hot.getSettings();
    const fields = this.dh.getFields();
    for (let col = 0; col < fields.length; col += 1) {
      if (slotNames.includes(fields[col].name)) {
        columns[col].readOnly = true;
      }
    }
    hot.updateSettings({ columns });
  }

  setTableReadOnly() {
    this.dh.hot.updateSettings({ readOnly: true });
    this.dh.hot.render();
  }

  setMaxRows(maxRows: number) {
    this.dh.hot.updateSettings({ maxRows });
  }

  setInvalidCells(invalidCells: Record<number, Record<number, string>>) {
    this.dh.invalid_cells = invalidCells;
    this.dh.hot.render();
  }

  getSlot(slotName: string, className: string) {
    // If this slot has been fully materialized into the class's attributes, return that
    const classAttributes = this.schema.classes?.[className]?.attributes;
    if (classAttributes && slotName in classAttributes) {
      return classAttributes[slotName];
    }
    // Otherwise return the top-level slot definition
    return this.schema.slots[slotName];
  }

  getSlotRank(slotName: string, className: string) {
    const slot = this.getSlot(slotName, className);
    if (!slot) {
      return 9999;
    }
    return slot.rank;
  }

  getSlotGroupRank(slotName: string, className: string) {
    const slot = this.getSlot(slotName, className);
    if (!slot || !slot.slot_group) {
      return 9999;
    }
    return this.getSlotRank(slot.slot_group, className);
  }

  getOrderedAttributeNames(className: string): string[] {
    return Object.keys(this.schema.classes[className].attributes).sort(
      (a, b) => {
        const aSlotGroupRank = this.getSlotGroupRank(a, className);
        const bSlotGroupRank = this.getSlotGroupRank(b, className);
        if (aSlotGroupRank !== bSlotGroupRank) {
          return aSlotGroupRank - bSlotGroupRank;
        }
        const aSlotRank = this.getSlotRank(a, className);
        const bSlotRank = this.getSlotRank(b, className);
        return aSlotRank - bSlotRank;
      },
    );
  }

  getHeaderRow(className: string): Record<string, string> {
    const orderedAttrNames = this.getOrderedAttributeNames(className);
    const attrs = this.schema.classes[className].attributes;
    const header = {} as Record<string, string>;
    orderedAttrNames.forEach((attrName) => {
      header[attrName] = attrs[attrName].title || attrs[attrName].name;
    });
    return header;
  }

  unflattenArrayValues(tableData: Record<string, any>[], className: string): Record<string, any>[] {
    return tableData.map((row) => Object.fromEntries(
      Object.entries(row).map(([key, value]) => {
        let unflattenedValue = value;
        if (
          this.schema.classes[className].attributes[key].multivalued
          && value.split
        ) {
          unflattenedValue = value.split(';').map((v: string) => v.trim());
        }
        return [key, unflattenedValue];
      }),
    ));
  }

  static flattenArrayValues(tableData: Record<string, any>[]) {
    if (!tableData) {
      return [];
    }
    return tableData.map((row) => Object.fromEntries(
      Object.entries(row).map(([key, value]) => {
        let flatValue = value;
        if (Array.isArray(value)) {
          flatValue = value.join('; ');
        }
        return [key, flatValue];
      }),
    ));
  }
}
