<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, type VehicleRecord } from '../api'
import { session } from '../session'

const router = useRouter()
const vehicles = ref<VehicleRecord[]>([])
const photos = ref<Record<number, string>>({})
const loading = ref(false)
const error = ref('')

async function loadVehicles() {
  const token = session.token.value
  if (!token) return
  loading.value = true
  error.value = ''
  try {
    vehicles.value = await api.vehicles(token)
    const loadedPhotos = await Promise.all(vehicles.value.map(async vehicle => {
      if (!vehicle.photo_filename) return [vehicle.id, ''] as const
      try { return [vehicle.id, await api.vehiclePhoto(token, vehicle.id)] as const }
      catch { return [vehicle.id, ''] as const }
    }))
    photos.value = Object.fromEntries(loadedPhotos)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'No se pudo cargar la lista de vehículos.'
  } finally {
    loading.value = false
  }
}

onMounted(() => { void loadVehicles() })
onUnmounted(() => Object.values(photos.value).forEach(url => url && URL.revokeObjectURL(url)))
</script>

<template>
  <div class="garage-app">
    <v-app-bar class="garage-appbar" flat>
      <v-btn icon="mdi-arrow-left" aria-label="Volver al panel" @click="router.push('/panel')" />
      <div class="brand-mini"><span class="brand-mini-icon"><v-icon icon="mdi-wrench-clock" /></span><span>pit<span class="brand-mini-dot">.</span>stop</span></div>
    </v-app-bar>
    <v-main>
      <v-container class="garage-page py-7 py-md-10">
        <div class="section-kicker">VEHÍCULOS</div>
        <div class="workshop-list-heading"><div><h1>Vehículos registrados</h1><p>Consulta cada vehículo, su fotografía y el cliente asociado.</p></div><v-avatar color="secondary" size="58"><v-icon icon="mdi-car-multiple" color="teal-darken-3" /></v-avatar></div>
        <v-alert v-if="error" type="error" variant="tonal" class="my-5">{{ error }}</v-alert>
        <v-progress-linear v-if="loading" indeterminate color="primary" class="my-5" />
        <div v-else-if="!error && vehicles.length" class="vehicle-list">
          <v-card v-for="vehicle in vehicles" :key="vehicle.id" class="vehicle-card" rounded="xl" elevation="0">
            <div class="vehicle-card-main">
              <img v-if="photos[vehicle.id]" class="vehicle-photo" :src="photos[vehicle.id]" :alt="`Fotografía de ${vehicle.make} ${vehicle.model}`" loading="lazy" />
              <div v-else class="vehicle-photo vehicle-photo-placeholder"><v-icon icon="mdi-car-off" size="42" /><span>Sin fotografía</span></div>
              <div class="vehicle-info">
                <div class="workshop-title-row"><h2>{{ vehicle.plate }}</h2><v-chip :color="vehicle.is_active ? 'success' : 'grey'" variant="tonal" size="small">{{ vehicle.status }}</v-chip></div>
                <div class="workshop-detail"><v-icon icon="mdi-car-info" /><span>{{ vehicle.make }} {{ vehicle.model }}<template v-if="vehicle.year"> · {{ vehicle.year }}</template><template v-if="vehicle.version"> · {{ vehicle.version }}</template></span></div>
                <div class="workshop-detail"><v-icon icon="mdi-account-outline" /><span><strong>Cliente</strong> {{ vehicle.client_name }}</span></div>
                <div class="workshop-detail"><v-icon icon="mdi-card-account-details-outline" /><span><strong>VIN</strong> {{ vehicle.vin || 'No especificado' }}</span></div>
                <div class="workshop-detail"><v-icon icon="mdi-palette-outline" /><span><strong>Color</strong> {{ vehicle.color || 'No especificado' }} · <strong>Kilometraje</strong> {{ vehicle.mileage ?? 'No especificado' }} km</span></div>
              </div>
            </div>
          </v-card>
        </div>
        <v-card v-else-if="!error" class="empty-team mt-6" rounded="xl" elevation="0"><v-icon icon="mdi-car-off" size="36" /><p>Aún no hay vehículos registrados.</p></v-card>
      </v-container>
    </v-main>
  </div>
</template>
