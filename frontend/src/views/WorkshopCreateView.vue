<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, type PostalEntry } from '../api'
import { session } from '../session'

const router = useRouter()
const token = session.token.value!
const form = ref({ name: '', rfc: '', contact_email: '', street: '', number: '', postal_code: '', state: '', municipality: '', neighborhood: '' })
const photo = ref<File | null>(null)
const busy = ref(false)
const error = ref('')
const message = ref('')
const postalMessage = ref('')
const postalBusy = ref(false)
const postalResults = ref<PostalEntry[]>([])
const selectedPostal = ref<number | null>(null)
const pendingPostal = ref<PostalEntry | null>(null)
const addressConfirm = ref(false)
const postalOptions = computed(() => postalResults.value.map((item, i) => ({ ...item, key: i, label: `${item.neighborhood} — ${item.municipality}, ${item.state} (${item.postal_code})` })))
watch(() => form.value.postal_code, () => { postalResults.value = []; selectedPostal.value = null; postalMessage.value = '' })
const required = (value: string) => Boolean(value?.trim()) || 'Campo obligatorio.'
const emailRule = (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || 'Escribe un correo válido.'
const rfcRule = (value: string) => /^(?:[A-ZÑ&]{3}|[A-ZÑ&]{4})\d{6}[A-Z0-9]{3}$/i.test(value.trim()) || 'Revisa la estructura del RFC.'
const postalRule = (value: string) => /^\d{5}$/.test(value) || 'Escribe cinco dígitos.'
const photoRule = (value: File | null) => !value || value.size <= 10 * 1024 * 1024 || 'La fotografía no puede superar 10 MB.'

function sameAddress(option: PostalEntry) {
  return form.value.state.trim().toLowerCase() === option.state.toLowerCase() &&
    form.value.municipality.trim().toLowerCase() === option.municipality.toLowerCase() &&
    form.value.neighborhood.trim().toLowerCase() === option.neighborhood.toLowerCase()
}
function applyPostal(option: PostalEntry) {
  const hasAddress = Boolean(form.value.state || form.value.municipality || form.value.neighborhood)
  if (hasAddress && !sameAddress(option)) { pendingPostal.value = option; addressConfirm.value = true; return }
  commitPostal(option)
}
function commitPostal(option: PostalEntry) {
  form.value.postal_code = option.postal_code; form.value.state = option.state
  form.value.municipality = option.municipality; form.value.neighborhood = option.neighborhood
  addressConfirm.value = false; selectedPostal.value = null; pendingPostal.value = null
}
async function lookupPostal() {
  error.value = ''; postalMessage.value = ''; postalResults.value = []
  if (!/^\d{5}$/.test(form.value.postal_code.trim())) { error.value = 'Escribe un código postal de cinco dígitos.'; return }
  postalBusy.value = true
  try {
    postalResults.value = await api.postalByCode(token, form.value.postal_code.trim())
    if (postalResults.value.length === 1) applyPostal(postalResults.value[0])
    else if (postalResults.value.length > 1) { selectedPostal.value = null; postalMessage.value = 'Hay varias colonias para este código postal. Selecciona la correcta.' }
    else postalMessage.value = 'No encontramos ese código postal en el catálogo. Puedes completar la dirección manualmente.'
  } catch (err) { error.value = err instanceof Error ? err.message : 'No se pudo consultar el catálogo postal.' }
  finally { postalBusy.value = false }
}
async function reverseSearch() {
  error.value = ''; postalMessage.value = ''; postalResults.value = []
  if (![form.value.state, form.value.municipality, form.value.neighborhood].every(value => value.trim())) { error.value = 'Completa estado, municipio y colonia para buscar el código postal.'; return }
  postalBusy.value = true
  try {
    postalResults.value = await api.postalReverse(token, form.value.state, form.value.municipality, form.value.neighborhood)
    if (postalResults.value.length === 1) applyPostal(postalResults.value[0])
    else if (postalResults.value.length > 1) { selectedPostal.value = null; postalMessage.value = 'Encontramos varios códigos postales. Selecciona la combinación correcta.' }
    else postalMessage.value = 'No encontramos esa dirección en el catálogo postal. Puedes capturar el código postal manualmente.'
  } catch (err) { error.value = err instanceof Error ? err.message : 'No se pudo consultar el catálogo postal.' }
  finally { postalBusy.value = false }
}
async function save() {
  error.value = ''; message.value = ''
  if (!photo.value) { error.value = 'Selecciona una fotografía del taller.'; return }
  if (photo.value.size > 10 * 1024 * 1024) { error.value = 'La fotografía no puede superar 10 MB.'; return }
  const body = new FormData()
  Object.entries(form.value).forEach(([key, value]) => body.append(key, value.trim()))
  body.append('photo', photo.value)
  busy.value = true
  try { const result = await api.createWorkshop(token, body); message.value = result.message; form.value = { name: '', rfc: '', contact_email: '', street: '', number: '', postal_code: '', state: '', municipality: '', neighborhood: '' }; photo.value = null }
  catch (err) { error.value = err instanceof Error ? err.message : 'No se pudo registrar el taller.' }
  finally { busy.value = false }
}
</script>

<template>
  <v-app><v-app-bar flat><v-btn icon="mdi-arrow-left" aria-label="Volver" @click="router.push('/panel')"/><v-toolbar-title>Dar de alta un taller</v-toolbar-title></v-app-bar>
    <v-main><v-container style="max-width: 900px" class="py-8"><h1 class="mb-2">Registro del taller mecánico</h1><p class="mb-6">Completa los datos y agrega una fotografía JPG, PNG o WebP de hasta 10 MB.</p>
      <v-alert v-if="message" type="success" variant="tonal" class="mb-4">{{ message }}</v-alert>
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert v-if="postalMessage" type="info" variant="tonal" class="mb-4">{{ postalMessage }}</v-alert>
      <v-card class="pa-5 pa-md-7" rounded="xl"><v-form @submit.prevent="save"><v-row dense>
        <v-col cols="12"><v-text-field v-model="form.name" label="Nombre del taller" :rules="[required]" required/></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.rfc" label="RFC" maxlength="13" :rules="[required, rfcRule]" required/></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.contact_email" label="Correo de contacto" type="email" :rules="[required, emailRule]" required/></v-col>
        <v-col cols="12" md="8"><v-text-field v-model="form.street" label="Calle" :rules="[required]" required/></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.number" label="Número" :rules="[required]" required/></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.postal_code" label="Código postal" maxlength="5" :rules="[required, postalRule]" @keydown.enter.prevent="lookupPostal" required><template #append-inner><v-btn icon="mdi-magnify" size="small" variant="text" aria-label="Buscar código postal" :loading="postalBusy" @click="lookupPostal"/></template></v-text-field></v-col>
        <v-col cols="12" md="8"><v-select v-if="postalResults.length > 1" v-model="selectedPostal" :items="postalOptions" item-title="label" item-value="key" label="Coincidencias del código postal" @update:model-value="index => index !== null && applyPostal(postalResults[index])"/></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.state" label="Estado" :rules="[required]" required/></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.municipality" label="Municipio o alcaldía" :rules="[required]" required/></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.neighborhood" label="Colonia" :rules="[required]" required/></v-col>
        <v-col cols="12"><v-btn variant="tonal" prepend-icon="mdi-map-search" :loading="postalBusy" @click="reverseSearch">Buscar código postal por dirección</v-btn><div v-if="!postalMessage && postalResults.length === 0" class="text-caption mt-2">Si el catálogo no encuentra la dirección, puedes completar o corregir los campos manualmente.</div></v-col>
        <v-col cols="12"><v-file-input v-model="photo" label="Fotografía del taller" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" :rules="[photoRule]" show-size prepend-icon="mdi-camera" required/></v-col>
      </v-row><div class="d-flex justify-end mt-3"><v-btn color="primary" type="submit" :loading="busy">Guardar taller</v-btn></div></v-form></v-card>
    </v-container></v-main>
    <v-dialog v-model="addressConfirm" max-width="480"><v-card class="pa-5" rounded="xl"><h2 class="text-h6">Actualizar dirección</h2><p class="my-4">La búsqueda encontró otra dirección. ¿Quieres reemplazar los datos actuales?</p><div class="d-flex justify-end ga-2"><v-btn variant="text" @click="addressConfirm = false; pendingPostal = null">Conservar datos</v-btn><v-btn color="primary" @click="pendingPostal && commitPostal(pendingPostal)">Actualizar dirección</v-btn></div></v-card></v-dialog>
  </v-app>
</template>
