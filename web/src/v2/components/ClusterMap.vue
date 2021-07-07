<script lang="ts">
import {
  computed,
  defineComponent, PropType, reactive, ref, toRef, watch, watchEffect,
} from '@vue/composition-api';

/**
 * LEAFLET imports
 */
import L, { Icon } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  LMap, LTileLayer, LMarker,
} from 'vue2-leaflet';
// @ts-ignore
import * as markerurl from 'leaflet/dist/images/marker-icon.png';
// @ts-ignore
import * as retinaurl from 'leaflet/dist/images/marker-icon-2x.png';
// @ts-ignore
import * as shadowurl from 'leaflet/dist/images/marker-shadow.png';
// @ts-ignore
import Vue2LeafletMarkerCluster from 'vue2-leaflet-markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
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

export default defineComponent({
  components: {
    LMap,
    LTileLayer,
    LMarker,
    'l-marker-cluster': Vue2LeafletMarkerCluster,
  },

  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      default: () => [],
    },
    height: {
      type: Number,
      default: 360,
    },
  },

  setup(props, { emit }) {
    const mapRef = ref();
    const mapProps = reactive({
      zoom: 3,
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      iconSize: 64,
      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
    });
    const mapData = ref([] as (EnvironmentGeospatialEntity & { latLng: L.LatLngExpression })[]);
    const mapCenter = computed(() => {
      const data: L.LatLngExpression[] = mapData.value.map(({ latLng }) => latLng);
      if (data.length === 0) return null;
      // @ts-ignore -- the type annotation for this method is wrong.
      return (new L.LatLngBounds(data)).pad(0.2);
    });

    async function getMapData() {
      const data = await api.getEnvironmentGeospatialAggregation(props.conditions);
      mapData.value = data.map((marker) => ({
        ...marker,
        latLng: L.latLng(marker.latitude, marker.longitude),
      }));
    }

    function updateBounds(bounds: L.LatLngBoundsExpression) {
      if (bounds && mapCenter.value?.contains(bounds)) {
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

    getMapData();

    watchEffect(() => {
      if (mapRef.value && mapCenter.value) {
        mapRef.value.fitBounds(mapCenter.value);
      }
    });
    watch([toRef(props, 'conditions')], getMapData);

    return {
      mapCenter,
      mapData,
      mapProps,
      mapRef,
      /* methods */
      updateBounds,
    };
  },
});
</script>

<template>
  <div>
    <l-map
      ref="mapRef"
      :style="{
        height: `${height}px`,
        width: '100%',
      }"
      @update:bounds="updateBounds"
    >
      <l-tile-layer
        :url="mapProps.url"
        :attribution="mapProps.attribution"
      />
      <l-marker-cluster>
        <l-marker
          v-for="(m, i) in mapData"
          :key="i"
          :lat-lng="m.latLng"
        />
      </l-marker-cluster>
    </l-map>
  </div>
</template>
