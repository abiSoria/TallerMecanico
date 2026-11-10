<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, type VehicleRecord, type VehicleUpdateData } from '../api'
import { session } from '../session'

const router = useRouter()
const token = session.token.value!
const canEditVehicles = computed(() => ['administrador', 'recepcionista'].includes(session.user.value?.role ?? ''))
const vehicles = ref<VehicleRecord[]>([])
const photos = ref<Record<number, string>>({})
const loading = ref(false)
const error = ref('')
const search = ref('')
const submittedSearch = ref('')
const detailDialog = ref(false)
const viewingVehicle = ref<VehicleRecord | null>(null)
const statusConfirmDialog = ref(false)
const statusBusy = ref(false)
const statusError = ref('')
const editDialog = ref(false)
const editingVehicle = ref<VehicleRecord | null>(null)
const editBusy = ref(false)
const editError = ref('')
const message = ref('')
const editValidationForm = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null)
type VehicleEditForm = Omit<VehicleUpdateData, 'year' | 'mileage'> & { year: number | null; mileage: number | null }
const emptyVehicleEdit = (): VehicleEditForm => ({ plate: '', make: '', model: '', year: null, version: '', color: '', mileage: null })
const editForm = ref<VehicleEditForm>(emptyVehicleEdit())
const requiredText = (value: unknown) => typeof value === 'string' && Boolean(value.trim()) || 'Campo obligatorio.'
const plateRule = (value: unknown) => typeof value === 'string' && /^[A-Z0-9-]{2,12}$/i.test(value.trim()) || 'Usa de 2 a 12 letras, números o guiones.'
const yearRule = (value: unknown) => typeof value === 'number' && Number.isInteger(value) && value >= 1886 && value <= new Date().getFullYear() + 1 || `Ingresa un año entre 1886 y ${new Date().getFullYear() + 1}.`
const mileageRule = (value: unknown) => typeof value === 'number' && Number.isInteger(value) && value >= 0 || 'El kilometraje debe ser un entero no negativo.'

function revokePhotos() {
  Object.values(photos.value).forEach(url => url && URL.revokeObjectURL(url))
  photos.value = {}
}

async function loadVehicles(searchTerm = '') {
  const token = session.token.value
  if (!token) return
  loading.value = true
  error.value = ''
  try {
    const records = await api.vehicles(token, searchTerm)
    const loadedPhotos = await Promise.all(records.map(async vehicle => {
      if (!vehicle.photo_filename) return [vehicle.id, ''] as const
      try { return [vehicle.id, await api.vehiclePhoto(token, vehicle.id)] as const }
      catch { return [vehicle.id, ''] as const }
    }))
    revokePhotos()
    vehicles.value = records
    photos.value = Object.fromEntries(loadedPhotos)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'No se pudo cargar la lista de vehículos.'
  } finally {
    loading.value = false
  }
}

async function submitSearch() {
  submittedSearch.value = search.value.trim()
  await loadVehicles(submittedSearch.value)
}

async function clearSearch() {
  search.value = ''
  submittedSearch.value = ''
  await loadVehicles()
}

function openDetails(vehicle: VehicleRecord) {
  viewingVehicle.value = vehicle
  statusError.value = ''
  detailDialog.value = true
}

function requestStatusChange() {
  if (!canEditVehicles.value || statusBusy.value || !viewingVehicle.value) return
  statusError.value = ''
  statusConfirmDialog.value = true
}

async function confirmStatusChange() {
  if (!canEditVehicles.value || statusBusy.value || !viewingVehicle.value) return
  const selected = viewingVehicle.value
  statusBusy.value = true
  statusError.value = ''
  try {
    const updated = await api.setVehicleActive(token, selected.id, !selected.is_active)
    viewingVehicle.value = updated
    vehicles.value = vehicles.value.map(vehicle => vehicle.id === updated.id ? updated : vehicle)
    statusConfirmDialog.value = false
    message.value = `El vehículo ${updated.plate} ahora está ${updated.is_active ? 'activo' : 'inactivo'}.`
  } catch (cause) {
    statusError.value = cause instanceof Error ? cause.message : 'No se pudo cambiar el estado del vehículo.'
  } finally {
    statusBusy.value = false
  }
}

function openEdit(vehicle: VehicleRecord) {
  if (!canEditVehicles.value) return
  editingVehicle.value = vehicle
  editForm.value = {
    plate: vehicle.plate,
    make: vehicle.make,
    model: vehicle.model,
    year: vehicle.year,
    version: vehicle.version ?? '',
    color: vehicle.color ?? '',
    mileage: vehicle.mileage,
  }
  editError.value = ''
  message.value = ''
  editDialog.value = true
}

async function saveVehicle() {
  if (editBusy.value || !editingVehicle.value || !canEditVehicles.value) return
  const validation = await editValidationForm.value?.validate()
  if (!validation?.valid) return
  editBusy.value = true
  editError.value = ''
  try {
    await api.updateVehicle(token, editingVehicle.value.id, {
      plate: editForm.value.plate.trim().toUpperCase(),
      make: editForm.value.make.trim().toLowerCase(),
      model: editForm.value.model.trim().toLowerCase(),
      year: Number(editForm.value.year),
      version: editForm.value.version.trim().toLowerCase(),
      color: editForm.value.color.trim().toLowerCase(),
      mileage: Number(editForm.value.mileage),
    })
    const plate = editForm.value.plate.trim().toUpperCase()
    editDialog.value = false
    editingVehicle.value = null
    message.value = `Los datos del vehículo ${plate} se actualizaron correctamente.`
    await loadVehicles(submittedSearch.value)
  } catch (cause) {
    editError.value = cause instanceof Error ? cause.message : 'No se pudieron guardar los cambios del vehículo.'
  } finally {
    editBusy.value = false
  }
}

onMounted(() => { void loadVehicles() })
onUnmounted(revokePhotos)
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
        <v-alert v-if="message" type="success" variant="tonal" closable class="mb-4" @click:close="message = ''">{{ message }}</v-alert>
        <v-alert v-if="error" type="error" variant="tonal" class="my-5">{{ error }}</v-alert>
        <form class="vehicle-search" role="search" @submit.prevent="submitSearch">
          <v-text-field
            v-model="search"
            label="Buscar por VIN, placa o ID"
            placeholder="Ej. 1HGCM82633A004352, ABC-123 o 42"
            prepend-inner-icon="mdi-magnify"
            hint="La búsqueda ignora mayúsculas, espacios y guiones."
            persistent-hint
            maxlength="64"
            :disabled="loading"
            autocomplete="off"
          />
          <v-btn type="submit" color="primary" size="large" :loading="loading" :disabled="loading">Buscar</v-btn>
          <v-btn v-if="submittedSearch" type="button" variant="text" :disabled="loading" @click="clearSearch">Limpiar</v-btn>
        </form>
        <p v-if="submittedSearch && !loading && !error && vehicles.length" class="vehicle-search-count" role="status">
          {{ vehicles.length }} {{ vehicles.length === 1 ? 'resultado' : 'resultados' }} para “{{ submittedSearch }}”.
        </p>
        <v-progress-linear v-if="loading" indeterminate color="primary" class="my-5" />
        <div v-else-if="!error && vehicles.length" class="vehicle-list">
          <v-card v-for="vehicle in vehicles" :key="vehicle.id" class="vehicle-card" rounded="xl" elevation="0">
            <div class="vehicle-card-main">
              <img v-if="photos[vehicle.id]" class="vehicle-photo" :src="photos[vehicle.id]" :alt="`Fotografía de ${vehicle.make} ${vehicle.model}`" loading="lazy" />
              <div v-else class="vehicle-photo vehicle-photo-placeholder"><v-icon icon="mdi-car-off" size="42" /><span>Sin fotografía</span></div>
              <div class="vehicle-info">
                <div class="workshop-title-row"><h2>{{ vehicle.plate }}</h2><v-chip :color="vehicle.is_active ? 'success' : 'error'" variant="tonal" size="small">{{ vehicle.status }}</v-chip></div>
                <div class="workshop-detail"><v-icon icon="mdi-identifier" /><span><strong>ID</strong> #{{ vehicle.id }}</span></div>
                <div class="workshop-detail"><v-icon icon="mdi-car-info" /><span>{{ vehicle.make }} {{ vehicle.model }}<template v-if="vehicle.year"> · {{ vehicle.year }}</template><template v-if="vehicle.version"> · {{ vehicle.version }}</template></span></div>
                <div class="workshop-detail"><v-icon icon="mdi-account-outline" /><span><strong>Cliente</strong> {{ vehicle.client_name }}</span></div>
                <div class="workshop-detail"><v-icon icon="mdi-card-account-details-outline" /><span><strong>VIN</strong> {{ vehicle.vin || 'No especificado' }}</span></div>
                <div class="workshop-detail"><v-icon icon="mdi-palette-outline" /><span><strong>Color</strong> {{ vehicle.color || 'No especificado' }} · <strong>Kilometraje</strong> {{ vehicle.mileage ?? 'No especificado' }} km</span></div>
              </div>
              <div class="d-flex flex-wrap ga-2"><v-btn variant="tonal" color="secondary" prepend-icon="mdi-eye-outline" class="vehicle-edit-button" @click="openDetails(vehicle)">Ver vehículo</v-btn><v-btn v-if="canEditVehicles" variant="tonal" color="primary" prepend-icon="mdi-pencil" class="vehicle-edit-button" @click="openEdit(vehicle)">Editar</v-btn></div>
            </div>
          </v-card>
        </div>
        <v-card v-else-if="!error && submittedSearch" class="empty-team mt-6" rounded="xl" elevation="0" role="status">
          <v-icon icon="mdi-magnify-close" size="36" />
          <p>No se encontraron vehículos para “{{ submittedSearch }}”.</p>
        </v-card>
        <v-card v-else-if="!error" class="empty-team mt-6" rounded="xl" elevation="0"><v-icon icon="mdi-car-off" size="36" /><p>Aún no hay vehículos registrados.</p></v-card>
      </v-container>
    </v-main>
    <v-dialog v-model="editDialog" max-width="760" persistent>
      <v-card class="dialog-card" rounded="xl">
        <v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-car-cog" /></span><span>Actualizar vehículo</span></v-card-title>
        <v-card-subtitle>Cliente asociado: <strong>{{ editingVehicle?.client_name }}</strong></v-card-subtitle>
        <v-card-text class="pt-5">
          <v-form ref="editValidationForm" @submit.prevent="saveVehicle">
            <v-row dense>
              <v-col cols="12" sm="6"><v-text-field :model-value="editingVehicle?.vin || 'No especificado'" label="VIN (no editable)" readonly /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="editForm.plate" label="Placa" maxlength="12" :rules="[requiredText, plateRule]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="editForm.make" label="Marca" maxlength="60" :rules="[requiredText]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="editForm.model" label="Modelo" maxlength="60" :rules="[requiredText]" required /></v-col>
              <v-col cols="12" sm="4"><v-text-field v-model.number="editForm.year" label="Año" type="number" :rules="[yearRule]" required /></v-col>
              <v-col cols="12" sm="4"><v-text-field v-model="editForm.version" label="Versión" maxlength="80" :rules="[requiredText]" required /></v-col>
              <v-col cols="12" sm="4"><v-text-field v-model="editForm.color" label="Color" maxlength="40" :rules="[requiredText]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model.number="editForm.mileage" label="Kilometraje" type="number" min="0" :rules="[mileageRule]" required /></v-col>
            </v-row>
            <v-alert v-if="editError" type="error" variant="tonal" class="mt-3">{{ editError }}</v-alert>
            <div class="dialog-actions mt-5"><v-btn variant="text" class="text-none" :disabled="editBusy" @click="editDialog = false">Cancelar</v-btn><v-btn color="primary" type="submit" rounded="lg" class="text-none" :loading="editBusy">Guardar cambios</v-btn></div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>
    <v-dialog v-model="detailDialog" max-width="620">
      <v-card class="dialog-card" rounded="xl">
        <v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-car-info" /></span><span>Ver vehículo</span></v-card-title>
        <v-card-text class="pt-5">
          <div v-if="viewingVehicle" class="d-flex flex-column ga-3">
            <img v-if="photos[viewingVehicle.id]" class="vehicle-photo mx-auto" :src="photos[viewingVehicle.id]" :alt="`Fotografía de ${viewingVehicle.make} ${viewingVehicle.model}`" />
            <div class="workshop-title-row"><h2>{{ viewingVehicle.plate }}</h2><v-chip :color="viewingVehicle.is_active ? 'success' : 'error'" variant="tonal">{{ viewingVehicle.status }}</v-chip></div>
            <p><strong>Cliente:</strong> {{ viewingVehicle.client_name }}</p>
            <p><strong>Vehículo:</strong> {{ viewingVehicle.make }} {{ viewingVehicle.model }}<template v-if="viewingVehicle.year"> · {{ viewingVehicle.year }}</template><template v-if="viewingVehicle.version"> · {{ viewingVehicle.version }}</template></p>
            <p><strong>VIN:</strong> {{ viewingVehicle.vin || 'No especificado' }}</p><p><strong>Color:</strong> {{ viewingVehicle.color || 'No especificado' }}</p><p><strong>Kilometraje:</strong> {{ viewingVehicle.mileage ?? 'No especificado' }} km</p>
            <v-alert v-if="statusError" type="error" variant="tonal">{{ statusError }}</v-alert>
            <div class="dialog-actions mt-2"><v-btn variant="text" :disabled="statusBusy" @click="detailDialog = false">Cerrar</v-btn><v-btn v-if="canEditVehicles" :color="viewingVehicle.is_active ? 'error' : 'success'" variant="tonal" :prepend-icon="viewingVehicle.is_active ? 'mdi-car-off' : 'mdi-car'" :disabled="statusBusy" @click="requestStatusChange">{{ viewingVehicle.is_active ? 'Desactivar vehículo' : 'Activar vehículo' }}</v-btn></div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
    <v-dialog v-model="statusConfirmDialog" max-width="440" persistent>
      <v-card class="dialog-card" rounded="xl">
        <v-card-title class="dialog-title"><span class="dialog-icon"><v-icon :icon="viewingVehicle?.is_active ? 'mdi-alert-circle-outline' : 'mdi-check-circle-outline'" /></span><span>Confirmar cambio de estado</span></v-card-title>
        <v-card-text class="pt-4">
          <p>¿Está seguro que desea {{ viewingVehicle?.is_active ? 'desactivar' : 'activar' }} el vehículo <strong>{{ viewingVehicle?.plate }}</strong>?</p>
          <div class="dialog-actions mt-5"><v-btn variant="text" :disabled="statusBusy" @click="statusConfirmDialog = false">Cancelar</v-btn><v-btn :color="viewingVehicle?.is_active ? 'error' : 'success'" :loading="statusBusy" @click="confirmStatusChange">Confirmar</v-btn></div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>
