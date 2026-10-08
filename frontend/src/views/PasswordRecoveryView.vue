<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { emailRule, passwordRule } from '../validation'

const route = useRoute()
const router = useRouter()
const resetToken = computed(() => typeof route.query.token === 'string' ? route.query.token : '')
const isReset = computed(() => Boolean(resetToken.value))
const email = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const message = ref('')
const completed = ref(false)
const required = (value: string) => Boolean(value) || 'Este campo es obligatorio.'
const confirmationRule = computed(() => (value: string) => value === newPassword.value || 'Las contraseñas no coinciden.')

async function requestReset() {
  loading.value = true; error.value = ''; message.value = ''
  try {
    const result = await api.requestPasswordReset(email.value.trim().toLowerCase())
    message.value = result.message
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'No pudimos procesar la solicitud. Inténtalo de nuevo.'
  } finally { loading.value = false }
}

async function saveNewPassword() {
  loading.value = true; error.value = ''
  try {
    await api.resetPassword(resetToken.value, newPassword.value)
    completed.value = true
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'No pudimos actualizar la contraseña. Solicita un enlace nuevo.'
  } finally { loading.value = false }
}
</script>

<template>
  <main class="recovery-page">
    <v-card class="dialog-card recovery-card" rounded="xl" elevation="2">
      <v-card-title class="dialog-title">
        <span class="dialog-icon"><v-icon :icon="isReset ? 'mdi-lock-reset' : 'mdi-email-lock-outline'" /></span>
        <span>{{ isReset ? 'Crear nueva contraseña' : 'Recuperar contraseña' }}</span>
      </v-card-title>
      <v-card-text class="pt-5">
        <template v-if="!isReset">
          <p class="form-subtitle">Escribe el correo asociado a tu cuenta. Te enviaremos un enlace para recuperar el acceso.</p>
          <v-form @submit.prevent="requestReset">
            <v-text-field v-model="email" label="Correo electrónico" type="email" autocomplete="email" :rules="[required, emailRule]" prepend-inner-icon="mdi-email-outline" required />
            <v-alert v-if="message" type="success" variant="tonal" class="mb-4">{{ message }}</v-alert>
            <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
            <v-btn color="primary" type="submit" size="large" block :loading="loading">Enviar instrucciones <v-icon end icon="mdi-arrow-right" /></v-btn>
          </v-form>
        </template>
        <template v-else-if="completed">
          <v-alert type="success" variant="tonal" class="mb-4">Tu contraseña se actualizó. Ya puedes iniciar sesión con la nueva contraseña.</v-alert>
        </template>
        <template v-else>
          <p class="form-subtitle">Elige una contraseña nueva para tu cuenta.</p>
          <v-form @submit.prevent="saveNewPassword">
            <v-text-field v-model="newPassword" label="Nueva contraseña" type="password" autocomplete="new-password" :rules="[required, passwordRule]" hint="12 o más caracteres con mayúscula, minúscula, número y símbolo." persistent-hint required />
            <v-text-field v-model="confirmPassword" label="Confirmar contraseña" type="password" autocomplete="new-password" :rules="[required, confirmationRule]" required />
            <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
            <v-btn color="primary" type="submit" size="large" block :loading="loading">Guardar contraseña <v-icon end icon="mdi-check" /></v-btn>
          </v-form>
        </template>
        <div class="text-center mt-5">
          <v-btn variant="text" class="text-none" @click="router.push('/ingresar')">Volver a iniciar sesión</v-btn>
        </div>
      </v-card-text>
    </v-card>
  </main>
</template>

<style scoped>
.recovery-page { min-height: 100vh; display: grid; place-items: center; padding: 1.25rem; background: radial-gradient(ellipse at 95% 5%, #7fe0d429, transparent 38%), #f4faf9; }
.recovery-card { width: min(100%, 480px); padding: 1rem; }
</style>
