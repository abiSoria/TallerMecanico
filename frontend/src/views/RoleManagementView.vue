<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError, api, type RoleRecord } from '../api'
import { session } from '../session'

const router = useRouter()
const token = session.token.value!
const rows = ref<RoleRecord[]>([])
const name = ref('')
const description = ref('')
const selected = ref<RoleRecord | null>(null)
const editName = ref('')
const editDescription = ref('')
const busy = ref(false)
const error = ref('')
const message = ref('')
const dialog = ref(false)

async function load() {
  try { rows.value = await api.roles(token) }
  catch (err) { error.value = err instanceof Error ? err.message : 'No se pudieron consultar los roles.' }
}
async function create() {
  busy.value = true; error.value = ''; message.value = ''
  try { await api.createRole(token, { name: name.value, description: description.value }); name.value = ''; description.value = ''; message.value = 'Rol creado correctamente.'; await load() }
  catch (err) { error.value = err instanceof Error ? err.message : 'No se pudo crear el rol.' }
  finally { busy.value = false }
}
function edit(row: RoleRecord) { selected.value = row; editName.value = row.name; editDescription.value = row.description ?? ''; dialog.value = true }
async function save() {
  if (!selected.value) return
  busy.value = true; error.value = ''
  try { await api.updateRole(token, selected.value.id, { name: editName.value, description: editDescription.value }); dialog.value = false; message.value = 'Cambios guardados.'; await load() }
  catch (err) { error.value = err instanceof ApiError ? err.message : 'No se pudo actualizar el rol.' }
  finally { busy.value = false }
}
async function suspend(row: RoleRecord) {
  if (!window.confirm(`¿Suspender el rol “${row.name}”?`)) return
  error.value = ''; message.value = ''
  try { const result = await api.suspendRole(token, row.id); message.value = result.message; await load() }
  catch (err) { error.value = err instanceof Error ? err.message : 'No se pudo suspender el rol.' }
}
onMounted(load)
</script>

<template>
  <v-app><v-app-bar flat><v-btn icon="mdi-arrow-left" aria-label="Volver" @click="router.push('/panel')"/><v-toolbar-title>Administrar roles</v-toolbar-title></v-app-bar>
    <v-main><v-container class="py-8" style="max-width: 1000px">
      <h1 class="mb-2">Roles del sistema</h1><p class="mb-6">Crea, consulta, actualiza o suspende roles.</p>
      <v-alert v-if="message" type="success" variant="tonal" class="mb-4">{{ message }}</v-alert>
      <v-alert v-if="error && !dialog" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-card class="pa-5 mb-6" rounded="xl"><h2 class="text-h6 mb-4">Crear rol</h2><v-form @submit.prevent="create"><v-text-field v-model="name" label="Nombre del rol" maxlength="40" required/><v-text-field v-model="description" label="Descripción" maxlength="200"/><v-btn type="submit" color="primary" :loading="busy">Crear rol</v-btn></v-form></v-card>
      <v-card rounded="xl"><v-table><thead><tr><th>Nombre</th><th>Descripción</th><th>Estado</th><th>Acciones</th></tr></thead><tbody><tr v-for="row in rows" :key="row.id"><td>{{ row.name }}</td><td>{{ row.description || '—' }}</td><td>{{ row.estatus }}<span class="d-block text-caption">{{ row.estatus_descripcion }}</span></td><td><v-btn size="small" variant="text" @click="edit(row)">Editar</v-btn><v-btn size="small" color="error" variant="text" :disabled="row.id_estatus === 2" @click="suspend(row)">Suspender</v-btn></td></tr></tbody></v-table></v-card>
    </v-container></v-main>
    <v-dialog v-model="dialog" max-width="540"><v-card class="pa-5" rounded="xl"><h2 class="text-h6 mb-4">Actualizar rol</h2><v-text-field v-model="editName" label="Nombre" maxlength="40"/><v-text-field v-model="editDescription" label="Descripción" maxlength="200"/><v-alert v-if="error" type="error" variant="tonal">{{ error }}</v-alert><div class="d-flex justify-end ga-2 mt-4"><v-btn variant="text" @click="dialog = false">Cancelar</v-btn><v-btn color="primary" :loading="busy" @click="save">Guardar cambios</v-btn></div></v-card></v-dialog>
  </v-app>
</template>
