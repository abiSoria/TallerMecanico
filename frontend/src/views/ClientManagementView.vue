<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, type ClientEditableData, type ClientRecord, type WorkshopRecord } from '../api'
import { session } from '../session'
import { emailRule, phoneRule } from '../validation'

const router = useRouter()
const token = session.token.value!
const clients = ref<ClientRecord[]>([])
const activeWorkshops = ref<WorkshopRecord[]>([])
const selectedClient = ref<ClientRecord | null>(null)
const editDialog = ref(false)
const associationDialog = ref(false)
const vehicleDialog = ref(false)
const selectedWorkshopId = ref<number | null>(null)
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const message = ref('')
const formError = ref('')
const vehicleError = ref('')
const vehicleBusy = ref(false)
const vehicleValidationForm = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null)
const vehicleForm = ref({ vin: '', plate: '', make: '', model: '', year: new Date().getFullYear(), version: '', color: '', mileage: 0 })
const vehiclePhoto = ref<File | null>(null)
const emptyClient = (): ClientEditableData => ({ full_name: '', street: '', number: '', neighborhood: '', municipality: '', state: '', primary_phone: '', alternate_phone: '', email: '' })
const editForm = ref<ClientEditableData>(emptyClient())
const required = (value: string) => Boolean(value?.trim()) || 'Campo obligatorio.'
const phoneRequired = (value: string) => Boolean(value?.trim()) && phoneRule(value) !== true || 'Ingresa un teléfono válido.'
const vehicleRequired = (value: string) => Boolean(value?.trim()) || 'Campo obligatorio.'
const vinRule = (value: string) => /^[A-Z0-9-]{5,32}$/i.test(value.trim()) || 'Usa de 5 a 32 letras, números o guiones.'
const plateRule = (value: string) => /^[A-Z0-9-]{2,12}$/i.test(value.trim()) || 'Usa de 2 a 12 letras, números o guiones.'
const yearRule = (value: number) => Number.isInteger(Number(value)) && Number(value) >= 1886 && Number(value) <= new Date().getFullYear() + 1 || `Ingresa un año entre 1886 y ${new Date().getFullYear() + 1}.`
const mileageRule = (value: number) => Number.isInteger(Number(value)) && Number(value) >= 0 || 'El kilometraje debe ser un número entero no negativo.'

function vehiclePhotoRule(file: File | null) {
  if (!file) return true
  if (file.size > 10 * 1024 * 1024) return 'La fotografía no puede superar 10 MiB.'
  const extension = file.name.split('.').pop()?.toLowerCase()
  const allowed = new Set(['jpg', 'jpeg', 'png', 'webp'])
  if (!extension || !allowed.has(extension) || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return 'Selecciona una imagen JPG, PNG o WebP válida.'
  return true
}

async function loadClients() {
  loading.value = true
  error.value = ''
  try {
    const [records, workshops] = await Promise.all([api.clients(token), api.workshops(token)])
    clients.value = records
    activeWorkshops.value = workshops.filter(workshop => workshop.id_estatus === 1)
  } catch (cause) { error.value = cause instanceof Error ? cause.message : 'No se pudieron cargar los clientes.' }
  finally { loading.value = false }
}

function openEdit(client: ClientRecord) {
  selectedClient.value = client
  editForm.value = {
    full_name: client.full_name, street: client.street, number: client.number,
    neighborhood: client.neighborhood, municipality: client.municipality, state: client.state,
    primary_phone: client.primary_phone, alternate_phone: client.alternate_phone, email: client.email,
  }
  error.value = ''
  formError.value = ''
  editDialog.value = true
}

async function saveClient() {
  if (busy.value || !selectedClient.value) return
  busy.value = true
  formError.value = ''
  try {
    await api.updateClient(token, selectedClient.value.id, editForm.value)
    editDialog.value = false
    message.value = 'Los datos del cliente se actualizaron correctamente.'
    await loadClients()
  } catch (cause) { formError.value = cause instanceof Error ? cause.message : 'No se pudieron guardar los cambios del cliente.' }
  finally { busy.value = false }
}

function openAssociation(client: ClientRecord) {
  selectedClient.value = client
  selectedWorkshopId.value = client.workshop_id
  error.value = ''
  associationDialog.value = true
}

async function associateWorkshop() {
  if (busy.value || !selectedClient.value || !selectedWorkshopId.value) return
  busy.value = true
  error.value = ''
  try {
    await api.associateClientWorkshop(token, selectedClient.value.id, selectedWorkshopId.value)
    associationDialog.value = false
    message.value = 'El cliente quedó asociado al taller activo.'
    await loadClients()
  } catch (cause) { error.value = cause instanceof Error ? cause.message : 'No se pudo asociar el cliente al taller.' }
  finally { busy.value = false }
}

async function deactivate(client: ClientRecord) {
  if (busy.value) return
  if (!window.confirm('¿Desactivar a ' + client.full_name + '? Sus datos y relaciones se conservarán.')) return
  busy.value = true
  error.value = ''
  try {
    const result = await api.deactivateClient(token, client.id)
    message.value = result.message
    await loadClients()
  } catch (cause) { error.value = cause instanceof Error ? cause.message : 'No se pudo desactivar al cliente.' }
  finally { busy.value = false }
}

function openVehicle(client: ClientRecord) {
  if (!client.is_active) return
  selectedClient.value = client
  vehicleForm.value = { vin: '', plate: '', make: '', model: '', year: new Date().getFullYear(), version: '', color: '', mileage: 0 }
  vehiclePhoto.value = null
  vehicleError.value = ''
  vehicleDialog.value = true
}

async function saveVehicle() {
  if (vehicleBusy.value || !selectedClient.value?.is_active) return
  const validation = await vehicleValidationForm.value?.validate()
  if (!validation?.valid) return
  const photoValidation = vehiclePhotoRule(vehiclePhoto.value)
  if (photoValidation !== true) { vehicleError.value = photoValidation; return }
  vehicleBusy.value = true
  vehicleError.value = ''
  const data = new FormData()
  for (const [key, value] of Object.entries(vehicleForm.value)) data.append(key, String(value))
  if (vehiclePhoto.value) data.append('photo', vehiclePhoto.value)
  try {
    const vehicle = await api.registerVehicle(token, selectedClient.value.id, data)
    vehicleDialog.value = false
    message.value = `Vehículo ${vehicle.plate} registrado y asociado a ${selectedClient.value.full_name}.`
    await loadClients()
  } catch (cause) { vehicleError.value = cause instanceof Error ? cause.message : 'No se pudo registrar el vehículo.' }
  finally { vehicleBusy.value = false }
}

onMounted(() => { void loadClients() })
</script>

<template>
  <div class="garage-app">
    <v-app-bar class="garage-appbar" flat>
      <v-btn icon="mdi-arrow-left" aria-label="Volver al panel" @click="router.push('/panel')" />
      <div class="brand-mini"><span class="brand-mini-icon"><v-icon icon="mdi-wrench-clock" /></span><span>pit<span class="brand-mini-dot">.</span>stop</span></div>
    </v-app-bar>
    <v-main>
      <v-container class="garage-page py-7 py-md-10">
        <div class="section-kicker">CLIENTES</div>
        <div class="workshop-list-heading"><div><h1>Administrar clientes</h1><p>Consulta, actualiza, asocia, registra vehículos o desactiva clientes.</p></div><v-avatar color="secondary" size="58"><v-icon icon="mdi-account-group" color="teal-darken-3" /></v-avatar></div>
        <v-alert v-if="message" type="success" variant="tonal" closable class="mb-4" @click:close="message = ''">{{ message }}</v-alert>
        <v-alert v-if="error && !associationDialog" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
        <v-progress-linear v-if="loading" indeterminate color="primary" class="my-5" />
        <v-card v-else rounded="xl" class="client-admin-card" elevation="0">
          <div class="client-table-scroll">
            <table class="client-admin-table">
              <thead><tr><th>Cliente</th><th>Contacto</th><th>Taller asociado</th><th>Estado</th><th>Acciones</th></tr></thead>
              <tbody>
                <tr v-for="client in clients" :key="client.id">
                  <td><strong>{{ client.full_name }}</strong><span class="client-address">{{ client.street }} {{ client.number }}, {{ client.neighborhood }}, {{ client.municipality }}, {{ client.state }}</span></td>
                  <td>{{ client.primary_phone }}<span class="client-address">{{ client.email }}</span></td>
                  <td>{{ client.workshop_name || 'Sin asociación' }}</td>
                  <td><v-chip :color="client.is_active ? 'success' : 'grey'" variant="tonal" size="small">{{ client.is_active ? 'Activo' : 'Inactivo' }}</v-chip></td>
                  <td><div class="d-flex flex-wrap ga-1"><v-btn size="small" variant="text" prepend-icon="mdi-pencil" class="text-none" @click="openEdit(client)">Editar</v-btn><v-btn size="small" variant="text" prepend-icon="mdi-domain-link" class="text-none" :disabled="!client.is_active || !activeWorkshops.length" @click="openAssociation(client)">Asociar a taller</v-btn><v-btn size="small" variant="text" prepend-icon="mdi-car-plus" class="text-none" :disabled="!client.is_active || vehicleBusy" @click="openVehicle(client)">Asociar vehículo</v-btn><v-btn size="small" variant="text" color="error" prepend-icon="mdi-account-off-outline" class="text-none" :disabled="!client.is_active || busy" @click="deactivate(client)">Desactivar</v-btn></div></td>
                </tr>
                <tr v-if="!clients.length"><td colspan="5" class="client-empty">Aún no hay clientes registrados.</td></tr>
              </tbody>
            </table>
          </div>
        </v-card>
      </v-container>
    </v-main>

    <v-dialog v-model="editDialog" max-width="760" persistent>
      <v-card class="dialog-card" rounded="xl">
        <v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-account-edit-outline" /></span><span>Editar cliente</span></v-card-title>
        <v-card-subtitle>Modifica únicamente los datos propios del cliente.</v-card-subtitle>
        <v-card-text class="pt-5"><v-form @submit.prevent="saveClient"><v-row dense>
          <v-col cols="12"><v-text-field v-model="editForm.full_name" label="Nombre completo" :rules="[required]" required /></v-col>
          <v-col cols="12" sm="8"><v-text-field v-model="editForm.street" label="Calle" :rules="[required]" required /></v-col>
          <v-col cols="12" sm="4"><v-text-field v-model="editForm.number" label="Número" :rules="[required]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="editForm.neighborhood" label="Colonia" :rules="[required]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="editForm.municipality" label="Municipio" :rules="[required]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="editForm.state" label="Estado" :rules="[required]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="editForm.primary_phone" label="Teléfono principal" type="tel" :rules="[required, phoneRequired]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="editForm.alternate_phone" label="Teléfono alterno" type="tel" :rules="[required, phoneRequired]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="editForm.email" label="Correo electrónico" type="email" :rules="[required, emailRule]" required /></v-col>
        </v-row>
        <v-alert v-if="formError" type="error" variant="tonal" class="mt-3">{{ formError }}</v-alert>
        <div class="dialog-actions mt-5"><v-btn variant="text" class="text-none" :disabled="busy" @click="editDialog = false">Cancelar</v-btn><v-btn color="primary" type="submit" rounded="lg" class="text-none" :loading="busy">Guardar cambios</v-btn></div>
        </v-form></v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="vehicleDialog" max-width="760" persistent>
      <v-card class="dialog-card" rounded="xl">
        <v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-car-plus" /></span><span>Asociar vehículo</span></v-card-title>
        <v-card-subtitle>Cliente: <strong>{{ selectedClient?.full_name }}</strong></v-card-subtitle>
        <v-card-text class="pt-5"><v-form ref="vehicleValidationForm" @submit.prevent="saveVehicle"><v-row dense>
          <v-col cols="12" sm="6"><v-text-field v-model="vehicleForm.vin" label="VIN" :rules="[vehicleRequired, vinRule]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="vehicleForm.plate" label="Placa" :rules="[vehicleRequired, plateRule]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="vehicleForm.make" label="Marca" :rules="[vehicleRequired]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model="vehicleForm.model" label="Modelo" :rules="[vehicleRequired]" required /></v-col>
          <v-col cols="12" sm="4"><v-text-field v-model.number="vehicleForm.year" label="Año" type="number" :rules="[yearRule]" required /></v-col>
          <v-col cols="12" sm="4"><v-text-field v-model="vehicleForm.version" label="Versión" :rules="[vehicleRequired]" required /></v-col>
          <v-col cols="12" sm="4"><v-text-field v-model="vehicleForm.color" label="Color" :rules="[vehicleRequired]" required /></v-col>
          <v-col cols="12" sm="6"><v-text-field v-model.number="vehicleForm.mileage" label="Kilometraje" type="number" min="0" :rules="[mileageRule]" required /></v-col>
          <v-col cols="12"><v-file-input v-model="vehiclePhoto" label="Fotografía (opcional)" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" prepend-icon="mdi-camera" show-size :rules="[vehiclePhotoRule]" /></v-col>
        </v-row>
        <v-alert v-if="vehicleError" type="error" variant="tonal" class="mt-3">{{ vehicleError }}</v-alert>
        <div class="dialog-actions mt-5"><v-btn variant="text" class="text-none" :disabled="vehicleBusy" @click="vehicleDialog = false">Cancelar</v-btn><v-btn color="primary" type="submit" rounded="lg" class="text-none" :loading="vehicleBusy">Guardar vehículo</v-btn></div>
        </v-form></v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="associationDialog" max-width="520">
      <v-card class="dialog-card" rounded="xl"><v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-domain-link" /></span><span>Asociar cliente a taller</span></v-card-title>
        <v-card-text class="pt-4"><p class="mb-4">Cliente: <strong>{{ selectedClient?.full_name }}</strong></p><v-select v-model="selectedWorkshopId" :items="activeWorkshops" item-title="name" item-value="id" label="Taller activo" :rules="[value => Boolean(value) || 'Selecciona un taller activo.']" required /><v-alert v-if="error" type="error" variant="tonal" class="mt-3">{{ error }}</v-alert><div class="dialog-actions mt-4"><v-btn variant="text" :disabled="busy" @click="associationDialog = false">Cancelar</v-btn><v-btn color="primary" :loading="busy" :disabled="!selectedWorkshopId" @click="associateWorkshop">Asociar</v-btn></div></v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>
