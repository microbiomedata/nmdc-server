import {
  Ref, ref, nextTick,
} from '@vue/composition-api';
import { debounce } from 'lodash';
import { DataHarmonizer, Footer } from 'data-harmonizer';

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

const EMSL = 'emsl';
const JGI_MG = 'jgi_mg';
const JGT_MT = 'jgi_mt';
export function getVariants(checkBoxes: string[], dataGenerated: boolean | undefined, base: string): string[] {
  const templates = [base];
  if (dataGenerated) {
    return templates;
  }
  if (checkBoxes.includes('mp-emsl') || checkBoxes.includes('mb-emsl') || checkBoxes.includes('nom-emsl')) {
    templates.push(EMSL);
  }
  if (checkBoxes.includes('mg-jgi')) {
    templates.push(JGI_MG);
  }
  if (checkBoxes.includes('mt-jgi')) {
    templates.push(JGT_MT);
  }
  return templates;
}

/**
 * A manifest of the options available in DataHarmonizer
 */
export const HARMONIZER_TEMPLATES: Record<string, {
  default: string;
  status: 'published' | 'disabled';
}> = {
  air: { default: 'air', status: 'published' },
  // bioscales: { default: 'bioscales', status: 'published' },
  'built environment': { default: 'built_env', status: 'published' },
  'host-associated': { default: 'host-associated', status: 'published' },
  'human-associated': { default: '', status: 'disabled' },
  'human-gut': { default: '', status: 'disabled' },
  'human-oral': { default: '', status: 'disabled' },
  'human-skin': { default: '', status: 'disabled' },
  'human-vaginal': { default: '', status: 'disabled' },
  'hydrocarbon resources-cores': {
    default: 'hcr-cores', status: 'published',
  },
  'hydrocarbon resources-fluids_swabs': {
    default: 'hcr-fluids-swabs', status: 'published',
  },
  'microbial mat_biofilm': {
    default: 'biofilm', status: 'published',
  },
  'miscellaneous natural or artificial environment': {
    default: 'misc-envs', status: 'published',
  },
  'plant-associated': {
    default: 'plant-associated', status: 'published',
  },
  sediment: {
    default: 'sediment', status: 'published',
  },
  soil: {
    default: 'soil', status: 'published',
  },
  wastewater_sludge: {
    default: 'wastewater_sludge', status: 'published',
  },
  water: {
    default: 'water', status: 'published',
  },
};

interface CellData {
  row: number,
  col: number,
  text: string,
}

export class HarmonizerApi {
  schemaSections: Ref<Record<string, Record<string, number>>>;

  ready: Ref<boolean>;

  goldEcosystemTree: any;

  dh: any;

  footer: any;

  selectedColumn: Ref<string>;

  schema: any;

  constructor() {
    this.schemaSections = ref({});
    this.ready = ref(false);
    this.selectedColumn = ref('');
  }

  async init(r: HTMLElement, templateName: string) {
    this.schema = (await import('./schema.json')).default;
    // Taken from https://gold.jgi.doe.gov/download?mode=biosampleEcosystemsJson
    // See also: https://gold.jgi.doe.gov/ecosystemtree
    this.goldEcosystemTree = (await import('./GoldEcosystemTree.json')).default;

    this.dh = new DataHarmonizer(r, {
      modalsRoot: document.querySelector('.harmonizer-style-container'),
      fieldSettings: this._getFieldSettings(),
      columnHelpEntries: ['column', 'description', 'guidance', 'examples'],
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
      this.selectedColumn.value = this.dh.getFields()[col].title;
    }, 200, { leading: true }));
    this.dh.hot.updateSettings({ search: true, customBorders: true });
    this.jumpToRowCol(0, 0);
  }

  refreshState() {
    this.schemaSections.value = this._getColumnCoordinates();
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

  exportJson() {
    return this.dh.getDataObjects(false);
  }

  scrollViewportTo(row: number, column: number) {
    this.dh.hot.scrollViewportTo(row, column);
  }

  jumpToRowCol(row: number, column: number) {
    this.dh.scrollTo(row, column);
  }

  launchReference() {
    this.dh.renderReference();
  }

  setupTemplate(folder: string) {
    this.dh.setupTemplate(folder);
  }

  validate() {
    this.dh.validate();
    this.refreshState();
    return this.dh.invalid_cells;
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
      callback();
    });
  }

  useTemplate(template: string) {
    if (!this.dh || !template) {
      return;
    }
    this.dh.useTemplate(template);
    this._postTemplateChange();
  }

  setColumnsReadOnly(columns: number[]) {
    const { hot } = this.dh;
    const rowCount = hot.countRows();
    columns.forEach((col) => {
      for (let row = 0; row < rowCount; row += 1) {
        hot.setCellMeta(row, col, 'readOnly', true);
      }
    });
    hot.render();
  }

  setMaxRows(maxRows: number) {
    this.dh.hot.updateSettings({ maxRows });
  }

  setInvalidCells(invalidCells: Record<number, Record<number, string>>) {
    this.dh.invalid_cells = invalidCells;
    this.dh.hot.render();
  }

  getSlot(slotName: string) {
    return this.schema.slots[slotName];
  }

  getSlotRank(slotName: string) {
    const slot = this.getSlot(slotName);
    if (!slot) {
      return 9999;
    }
    return slot.rank;
  }

  getSlotGroupRank(slotName: string) {
    const slot = this.getSlot(slotName);
    if (!slot || !slot.slot_group) {
      return 9999;
    }
    return this.getSlotRank(slot.slot_group);
  }

  getOrderedAttributeNames(template: string) {
    return Object.keys(this.schema.classes[template].attributes).sort(
      (a, b) => {
        const aSlotGroupRank = this.getSlotGroupRank(a);
        const bSlotGroupRank = this.getSlotGroupRank(b);
        if (aSlotGroupRank !== bSlotGroupRank) {
          return aSlotGroupRank - bSlotGroupRank;
        }
        const aSlotRank = this.getSlotRank(a);
        const bSlotRank = this.getSlotRank(b);
        return aSlotRank - bSlotRank;
      },
    );
  }

  getHeaderRow(template: string) {
    const orderedAttrNames = this.getOrderedAttributeNames(template);
    const attrs = this.schema.classes[template].attributes;
    const header = {} as Record<string, string>;
    orderedAttrNames.forEach((attrName) => {
      header[attrName] = attrs[attrName].title || attrs[attrName].name;
    });
    return header;
  }

  unflattenArrayValues(tableData: Record<string, any>[], template: string) {
    return tableData.map((row) => Object.fromEntries(
      Object.entries(row).map(([key, value]) => {
        let unflattenedValue = value;
        if (this.schema.classes[template].attributes[key].multivalued) {
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
