<script setup lang="ts">
import {
  computed, reactive, ref, toRef, watch, onMounted, nextTick,
} from 'vue';

/**
 * LEAFLET imports
 */
import L, { Icon } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import {
  LMap, LTileLayer,
} from '@vue-leaflet/vue-leaflet';
// @ts-ignore
import markerurl from 'leaflet/dist/images/marker-icon.png';
// @ts-ignore
import retinaurl from 'leaflet/dist/images/marker-icon-2x.png';
// @ts-ignore
import shadowurl from 'leaflet/dist/images/marker-shadow.png';
/**
 * END LEAFLET
 */

import { api, Condition, EnvironmentGeospatialEntity } from '@/data/api';

/**
 * LEAFLET icon missing hack fix
 * https://vue2-leaflet.netlify.app/quickstart/#marker-icons-are-missing
 */
type D = Icon.Default & {
  _getIconUrl?: string;
};

delete (Icon.Default.prototype as D)._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: retinaurl,
  iconUrl: markerurl,
  shadowUrl: shadowurl,
});
/**
 * END icon hack
 */

const props = withDefaults(defineProps<{
  conditions?: Condition[];
  height?: number;
  vistab?: number | null;
}>(), {
  conditions: () => [],
  height: 360,
  vistab: null,
});

const emit = defineEmits<{
  (e: 'selected', value: Condition[]): void;
}>();

const mapRef = ref();
const mapReady = ref(false);
const isLoading = ref(true);
const errorMessage = ref<string | null>(null);
const markerClusterGroup = ref<any>(null);
const mapProps = reactive({
  bounds: null as L.LatLngBoundsExpression | null,
  zoom: 3,
  url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  iconSize: 64,
  attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
});
const mapData = ref(
  [] as (EnvironmentGeospatialEntity & { latLng: L.LatLngExpression, key: string })[],
);
const mapCenter = computed(() => {
  const data: L.LatLngExpression[] = mapData.value.map(({ latLng }) => latLng);
  if (data.length === 0) return null;
  // @ts-ignore -- the type annotation for this method is wrong.
  return (new L.LatLngBounds(data));
});

async function getMapData() {
  try {
    if (props.vistab === 1) {
      // Don't update map data if ENVIRONMENT tab is clicked
      return;
    }
    isLoading.value = true;
    await new Promise<void>((res) => {
      window.setTimeout(res, 300);
    });
    const data = await api.getEnvironmentGeospatialAggregation(props.conditions);
    const values: any[] = [];
    data.forEach((cluster, index) => {
      if (cluster.latitude && cluster.longitude) {
        for (let i = 0; i < cluster.count; i += 1) {
          values.push({
            ...cluster,
            key: `${index}_${i}`,
            latLng: L.latLng(cluster.latitude, cluster.longitude),
          });
        }
      }
    });
    mapData.value = values;
  } catch (_error) {
    errorMessage.value = 'Could not load map data';
  } finally {
    isLoading.value = false;
  }
}

function updateMarkers() {
  const leafletMap = mapRef.value?.leafletObject;
  if (!leafletMap || !mapReady.value) return;

  // Remove existing cluster group if it exists
  if (markerClusterGroup.value) {
    leafletMap.removeLayer(markerClusterGroup.value);
  }

  // Create new marker cluster group
  // @ts-ignore - MarkerClusterGroup is added by leaflet.markercluster plugin
  markerClusterGroup.value = L.markerClusterGroup();

  // Add markers to the cluster group
  mapData.value.forEach((m) => {
    const marker = L.marker(m.latLng);
    const popupContent = `
      <h3>Sample Collection</h3>
      <ul class="pl-4">
        <li>Ecosystem: ${m.ecosystem || 'N/A'}</li>
        <li>Ecosystem Category: ${m.ecosystem_category || 'N/A'}</li>
        <li>Latitude: ${m.latitude}</li>
        <li>Longitude: ${m.longitude}</li>
      </ul>
    `;
    marker.bindPopup(popupContent);
    markerClusterGroup.value.addLayer(marker);
  });

  // Add the cluster group to the map
  leafletMap.addLayer(markerClusterGroup.value);

  // Fit bounds if we have data
  if (mapData.value.length > 0 && mapCenter.value) {
    const fitBoundsOptions = {
      padding: [20, 20],
      maxZoom: 5,
    };
    leafletMap.fitBounds(mapCenter.value, fitBoundsOptions);
  }
}

function updateBounds() {
  const { bounds } = mapProps;
  if (bounds) {
    emit('selected', [
      {
        field: 'latitude',
        op: 'between',
        value: [
          //  @ts-ignore
          bounds._southWest.lat, bounds._northEast.lat,
        ],
        table: 'biosample',
      },
      {
        field: 'longitude',
        op: 'between',
        value: [
          //  @ts-ignore
          bounds._southWest.lng, bounds._northEast.lng,
        ],
        table: 'biosample',
      },
    ]);
  }
}

function onMapReady() {
  // Add a small delay to ensure the map is fully initialized
  setTimeout(() => {
    mapReady.value = true;
  }, 100);
}

onMounted(async () => {
  await nextTick();
  // Wait for map to be ready before loading data
  if (!mapReady.value) {
    setTimeout(() => {
      if (mapReady.value) {
        getMapData();
      }
    }, 200);
  } else {
    getMapData();
  }
});

// Watch for map data changes and update markers
watch(mapData, () => {
  if (mapReady.value) {
    nextTick(() => {
      updateMarkers();
    });
  }
});

// Watch for map ready state
watch(mapReady, (ready) => {
  if (ready && mapData.value.length > 0) {
    nextTick(() => {
      updateMarkers();
    });
  }
});

watch([toRef(props, 'conditions')], () => {
  if (mapReady.value) {
    getMapData();
  }
});
</script>

<template>
  <div style="position: relative">
    <div
      v-if="isLoading || errorMessage"
      class="d-flex justify-center align-center"
      :style="{
        position: 'absolute',
        inset: 0,
        zIndex: 2,
        height: `${height}px`,
        background: 'rgba(255,255,255,0.7)',
      }"
    >
      <v-progress-circular
        v-if="isLoading"
        indeterminate
        color="primary"
      />
      <div v-else>
        {{ errorMessage }}
      </div>
    </div>
    <v-btn
      small
      color="primary"
      :disabled="isLoading || errorMessage ? true : false"
      :style="{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        zIndex: 2,
      }"
      @click="updateBounds"
    >
      Search this region
    </v-btn>
    <l-map
      ref="mapRef"
      :max-bounds="[[[-85, -180], [85, 180]]]"
      :style="{
        height: `${height}px`,
        width: '100%',
        zIndex: 1,
      }"
      @ready="onMapReady"
      @update:bounds="mapProps.bounds = $event"
    >
      <l-tile-layer
        :url="mapProps.url"
        :attribution="mapProps.attribution"
        :options="{
          maxZoom: 22,
          maxNativeZoom: 18,
        }"
      />
    </l-map>
  </div>
</template>

<style>
/* If the map is rendered in a <v-card>, long numbers within the cluster markers will wrap across
 * multiple lines. This forces the text to overflow and not wrap.
 */
.marker-cluster {
  overflow-wrap: normal;
  white-space: nowrap;
}
</style>
