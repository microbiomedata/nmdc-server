import {
  computed, Ref, ref, nextTick,
} from '@vue/composition-api';
import { debounce, has } from 'lodash';
import hot from 'handsontable';
import xlsx from 'xlsx';
import HarmonizerTemplateText from 'sheets_and_friends/docs/linkml.html';

const VariationMap = {
  /** A mapping of the templates to the superset of checkbox options they work for. */
  emsl: new Set(['mp-emsl', 'mb-emsl', 'nom-emsl']),
  jgi_mg: new Set(['mg-jgi']),
  emsl_jgi_mg: new Set(['mp-emsl', 'mb-emsl', 'nom-emsl', 'mg-jgi']),
};

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
  bioscales: { default: 'bioscales', status: 'published', variations: [] },
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
    default: 'soil', status: 'published', variations: ['emsl', 'emsl_jgi_mg', 'jgi_mg'],
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

  dh: any;

  toolbar: any;

  selectedColumn: Ref<string>;

  constructor() {
    this.validationErrors = ref({});
    this.schemaSections = ref({});
    this.ready = ref(false);
    this.selectedColumn = ref('');
    this.validationErrorGroups = computed(() => Object.keys(this.validationErrors.value));
  }

  async init(r: HTMLElement, templateName: string) {
    // @ts-ignore
    window.Handsontable = hot;
    // @ts-ignore
    window.XLSX = xlsx;

    // eslint-disable-next-line no-param-reassign
    r.innerHTML = HarmonizerTemplateText;
    // eslint-disable-next-line no-param-reassign
    const myDHGrid = document.getElementById('data-harmonizer-grid');
    const myDHToolbar = document.getElementById('data-harmonizer-toolbar');
    const myDHFooter = document.getElementById('data-harmonizer-footer');

    // eslint-disable-next-line no-new-object
    this.dh = new Object(DataHarmonizer);
    // eslint-disable-next-line no-new-object
    this.toolbar = new Object(DataHarmonizerToolbar);
    await this.dh.init(myDHGrid, myDHFooter, TEMPLATES);
    await this.toolbar.init(this.dh, myDHToolbar);

    // Picks first template in dh menu if none given in URL.
    this.dh.schema = SCHEMA;

    await this.dh.processTemplate(templateName);
    this.dh.schema_name = 'nmdc';
    this.dh.template_name = templateName;
    this.dh.template_path = `nmdc/${templateName}`;
    await this.dh.createHot();
    this.dh.hot.addHook('afterSelection', debounce((_, col: number) => {
      this.selectedColumn.value = this.dh.getFields()[col].title;
    }, 200, { leading: true }));
    this.dh.hot.updateSettings({ search: true, customBorders: true });
    await this.toolbar.refresh();
    // @ts-ignore
    window.dh = this.dh;

    // Erase unusued toolbar
    $('#data-harmonizer-toolbar-inset').children().slice(0, 6).attr('style', 'display:none !important');
    $('#data-harmonizer-toolbar')?.hide();
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
    if (['all', 'required', 'recommended'].includes(value)) {
      this.dh.changeColVisibility(`show-${value}-cols-dropdown-item`);
    } else {
      const ptr = Object.keys(this._getColumnCoordinates()).indexOf(value);
      this.dh.changeColVisibility(`show-section-${ptr}`);
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

  exportJson() {
    return [...this.dh.getFlatHeaders(), ...this.dh.getTrimmedData()];
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

  openFile(file: File) {
    if (!file) return;
    const ext = file.name.split('.').pop();
    if (!ext) return;
    const acceptedExts = ['xlsx', 'xls', 'tsv', 'csv'];
    if (!acceptedExts.includes(ext)) {
      const errMsg = `Only ${acceptedExts.join(', ')} files are supported`;
      $('#open-err-msg').text(errMsg);
      $('#open-error-modal').modal('show');
    } else {
      this.dh.invalid_cells = {};
      this.dh.runBehindLoadingScreen(this.dh.openFile, [this.dh, file]);
      $('#file_name_display').text(file.name);
    }
    $('#next-error-button,#no-error-button').hide();
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
