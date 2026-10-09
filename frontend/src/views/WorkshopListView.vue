<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, type WorkshopRecord } from '../api'
import { session } from '../session'

const router = useRouter()
const workshops = ref<WorkshopRecord[]>([])
const photos = ref<Record<number, string>>({})
const loading = ref(false)
const error = ref('')
const token = session.token.value!
async function loadWorkshops() {
  loading.value = true
  error.value = ''
  try {
    workshops.value = await api.workshops(token)
    const loadedPhotos = await Promise.all(workshops.value.map(async workshop => {
      try { return [workshop.id, await api.workshopPhoto(token, workshop.id)] as const }
      catch { return [workshop.id, ''] as const }
    }))
    photos.value = Object.fromEntries(loadedPhotos)
  }
  catch (cause) { error.value = cause instanceof Error ? cause.message : 'No se pudo cargar la lista de talleres.' }
  finally { loading.value = false }
}

onMounted(() => { void loadWorkshops() })
onUnmounted(() => Object.values(photos.value).forEach(url => url && URL.revokeObjectURL(url)))
</script>

<template>
  <div class="garage-app">
    <v-app-bar class="garage-appbar" flat>
      <v-btn icon="mdi-arrow-left" aria-label="Volver al panel" @click="router.push('/panel')" />
      <div class="brand-mini"><span class="brand-mini-icon"><v-icon icon="mdi-wrench-clock" /></span><span>pit<span class="brand-mini-dot">.</span>stop</span></div>
      <v-spacer />
      <v-btn variant="tonal" rounded="lg" prepend-icon="mdi-domain-plus" class="text-none mr-3" @click="router.push('/talleres/alta')">Dar de alta taller</v-btn>
    </v-app-bar>
    <v-main>
      <v-container class="garage-page py-7 py-md-10">
        <div class="section-kicker">TALLERES</div>
        <div class="workshop-list-heading"><div><h1>Talleres registrados</h1><p>Consulta los talleres dados de alta y su estado actual.</p></div><v-avatar color="secondary" size="58"><v-icon icon="mdi-domain" color="teal-darken-3" /></v-avatar></div>
        <v-alert v-if="error" type="error" variant="tonal" class="my-5">{{ error }}</v-alert>
        <v-progress-linear v-if="loading" indeterminate color="primary" class="my-5" />
        <div v-else-if="!error && workshops.length" class="workshop-list">
          <v-card v-for="workshop in workshops" :key="workshop.id" class="workshop-card" rounded="xl" elevation="0">
            <div class="workshop-card-main">
              <img v-if="photos[workshop.id]" class="workshop-photo" :src="photos[workshop.id]" :alt="`Fotografía de ${workshop.name}`" loading="lazy" />
              <div v-else class="workshop-photo workshop-photo-placeholder"><v-icon icon="mdi-image-off-outline" size="38" /></div>
              <div class="workshop-info">
                <div class="workshop-title-row"><h2>{{ workshop.name }}</h2><v-chip :color="workshop.id_estatus === 1 ? 'success' : 'grey'" variant="tonal" size="small">{{ workshop.status }}</v-chip></div>
                <div class="workshop-detail"><v-icon icon="mdi-card-account-details-outline" /><span><strong>RFC</strong> {{ workshop.rfc }}</span></div>
                <div class="workshop-detail"><v-icon icon="mdi-email-outline" /><span>{{ workshop.contact_email }}</span></div>
                <div class="workshop-detail workshop-address"><v-icon icon="mdi-map-marker-outline" /><span>{{ workshop.street }} {{ workshop.number }}, {{ workshop.neighborhood }}<br />{{ workshop.municipality }}, {{ workshop.state }} · CP {{ workshop.postal_code }}</span></div>
              </div>
            </div>
          </v-card>
        </div>
        <v-card v-else-if="!error" class="empty-team mt-6" rounded="xl" elevation="0"><v-icon icon="mdi-domain-off" size="36" /><p>Aún no hay talleres registrados.</p><v-btn color="primary" variant="tonal" rounded="lg" prepend-icon="mdi-domain-plus" @click="router.push('/talleres/alta')">Dar de alta taller</v-btn></v-card>
      </v-container>
    </v-main>
  </div>
</template>
