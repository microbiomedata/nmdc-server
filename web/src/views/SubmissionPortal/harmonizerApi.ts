import { computed, Ref, ref } from '@vue/composition-api';
import { debounce, has } from 'lodash';
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

const VariationMap = {
  /** A mapping of the templates to the superset of checkbox options they work for. */
  emsl: new Set(['mp-emsl', 'mb-emsl', 'nom-emsl']),
  jgi_mg: new Set(['mg-jgi']),
  emsl_jgi_mg: new Set(['mp-emsl', 'mb-emsl', 'nom-emsl', 'mg-jgi']),
};
// Variations should be in matching order.
// In other words, attempt to match 'emsl' before 'emsl_jgi_mg'
const allVariations: (keyof typeof VariationMap)[] = ['emsl', 'jgi_mg', 'emsl_jgi_mg'];

export function getVariant(checkBoxes: string[], variations: (keyof typeof VariationMap)[], base: string) {
  if (checkBoxes.length === 0) {
    return base;
  }
  const variationStr = variations.find((v) => {
    const vSet = VariationMap[v];
    return checkBoxes.every((elem) => vSet.has(elem));
  });
  if (variationStr) {
    return `${base}_${variationStr}`;
  }
  return base;
}

/**
 * A manifest of the options available in DataHarmonizer
 */
export const HARMONIZER_TEMPLATES: Record<string, {
  default: string;
  status: String;
  variations: (keyof typeof VariationMap)[];
}> = {
  air: { default: 'air', status: 'published', variations: [] },
  // bioscales: { default: 'bioscales', status: 'published', variations: [] },
  'built environment': { default: 'built_env', status: 'published', variations: [] },
  'host-associated': { default: 'host-associated', status: 'published', variations: [] },
  'human-associated': { default: '', status: 'disabled', variations: [] },
  'human-gut': { default: '', status: 'disabled', variations: [] },
  'human-oral': { default: '', status: 'disabled', variations: [] },
  'human-skin': { default: '', status: 'disabled', variations: [] },
  'human-vaginal': { default: '', status: 'disabled', variations: [] },
  'hydrocarbon resources-cores': {
    default: 'hcr-cores', status: 'published', variations: [],
  },
  'hydrocarbon resources-fluids_swabs': {
    default: 'hcr-fluids-swabs', status: 'published', variations: [],
  },
  'microbial mat_biofilm': {
    default: 'biofilm', status: 'published', variations: [],
  },
  'miscellaneous natural or artificial environment': {
    default: 'misc-envs', status: 'published', variations: [],
  },
  'plant-associated': {
    default: 'plant-associated', status: 'published', variations: [],
  },
  sediment: {
    default: 'sediment', status: 'published', variations: [],
  },
  soil: {
    default: 'soil', status: 'published', variations: allVariations,
  },
  wastewater_sludge: {
    default: 'wastewater_sludge', status: 'published', variations: [],
  },
  water: {
    default: 'water', status: 'published', variations: [],
  },
};

interface ValidationErrors {
  [error: string]: [number, number][],
}

export class HarmonizerApi {
  validationErrors: Ref<ValidationErrors>;

  validationErrorGroups: Ref<string[]>;

  schemaSections: Ref<Record<string, Record<string, number>>>;

  ready: Ref<boolean>;

  goldEcosystemTree: any;

  dh: any;

  footer: any;

  selectedColumn: Ref<string>;

  constructor() {
    this.validationErrors = ref({});
    this.schemaSections = ref({});
    this.ready = ref(false);
    this.selectedColumn = ref('');
    this.validationErrorGroups = computed(() => Object.keys(this.validationErrors.value));
  }

  async init(r: HTMLElement, templateName: string) {
    const schema = (await import('./schema.json')).default;
    // Taken from https://gold.jgi.doe.gov/download?mode=biosampleEcosystemsJson
    // See also: https://gold.jgi.doe.gov/ecosystemtree
    this.goldEcosystemTree = (await import('./GoldEcosystemTree.json')).default;

    this.dh = new DataHarmonizer(r, {
      modalsRoot: document.querySelector('.harmonizer-style-container'),
      fieldSettings: this._getFieldSettings(),
    });
    this.footer = new Footer(document.querySelector('#harmonizer-footer-root'), this.dh);
    this.dh.useSchema(schema, [], templateName);

    this.dh.hot.addHook('afterSelection', debounce((_, col: number) => {
      this.selectedColumn.value = this.dh.getFields()[col].title;
    }, 200, { leading: true }));

    this.ready.value = true;
    this.jumpToRowCol(0, 0);
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

  refreshState() {
    this.schemaSections.value = this._getColumnCoordinates();
    const remapped: ValidationErrors = {};
    const invalid: Record<number, Record<number, string>> = this.dh.invalid_cells;
    if (Object.keys(invalid).length) {
      remapped['All Errors'] = [];
    }
    Object.entries(invalid).forEach(([row, val]) => {
      Object.entries(val).forEach(([col, text]) => {
        const entry: [number, number] = [parseInt(row, 10), parseInt(col, 10)];
        const issue = text || 'Validation Error';
        if (has(remapped, issue)) {
          remapped[issue].push(entry);
        } else {
          remapped[issue] = [entry];
        }
        remapped['All Errors'].push(entry);
      });
    });
    this.validationErrors.value = remapped;
  }

  async loadData(data: any[][]) {
    await this.dh.hot.loadData(data);
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

  exportJson() {
    return [...this.dh.getFlatHeaders(), ...this.dh.getTrimmedData()];
  }

  jumpToRowCol(row: number, column: number) {
    this.dh.scrollTo(row, column);
  }

  launchReference() {
    this.dh.renderReference();
  }

  openFile(file: File) {
    if (!file) return;
    const ext = file.name.split('.').pop();
    if (!ext) return;
    const acceptedExts = ['xlsx', 'xls', 'tsv', 'csv'];
    if (!acceptedExts.includes(ext)) {
      // TODO: #open-error-modal not present because Toolbar component is not being used.
      // Display this error differently?
      //
      // const errMsg = `Only ${acceptedExts.join(', ')} files are supported`;
      // $('#open-err-msg').text(errMsg);
      // $('#open-error-modal').modal('show');
    } else {
      this.dh.invalid_cells = {};
      this.dh.runBehindLoadingScreen(this.dh.openFile, [file]);
    }
    this.dh.current_selection = [null, null, null, null];
  }

  setupTemplate(folder: string) {
    this.dh.setupTemplate(folder);
  }

  validate() {
    this.dh.validate();
    this.refreshState();
    return Object.keys(this.validationErrors).length === 0;
  }
}
