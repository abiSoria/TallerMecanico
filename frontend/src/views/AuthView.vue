<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { session } from '../session'
import { emailRule, nameRule, passwordRule, phoneRule } from '../validation'

const router = useRouter()
const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const fullName = ref('')
const phone = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const rules = { required: (v: string) => Boolean(v) || 'Este campo es obligatorio.', email: emailRule, name: nameRule, phone: phoneRule, password: passwordRule }
const confirmationRule = computed(() => (v: string) => v === password.value || 'Las contraseñas no coinciden.')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const result = mode.value === 'login'
      ? await api.login(email.value.trim().toLowerCase(), password.value)
      : await api.register({ full_name: fullName.value.trim(), email: email.value.trim().toLowerCase(), password: password.value, ...(phone.value.trim() ? { phone: phone.value.trim() } : {}) })
    session.establish(result.access_token, result.user)
    await router.push('/panel')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'No se pudo completar la solicitud.'
  } finally { loading.value = false }
}

function changeMode(next: 'login' | 'register') {
  mode.value = next
  error.value = ''
  password.value = ''
  confirmPassword.value = ''
}
</script>

<template>
  <main class="auth-shell">
    <section class="brand-panel">
      <div class="brand-mark"><span class="brand-mark-icon"><v-icon icon="mdi-wrench-clock" size="25" /></span><span>pit<span class="brand-mark-dot">.</span>stop</span><span class="brand-mark-label">TALLER MECÁNICO</span></div>
      <div class="brand-copy">
        <div class="brand-kicker"><i /> SERVICIO CON BUENA ENERGÍA</div>
        <h1>Tu vehículo, en buenas manos.</h1>
        <p>La tranquilidad también viene de saber qué está pasando. Aquí empieza el seguimiento de tu visita al taller.</p>
      </div>
      <div class="brand-scene" aria-hidden="true">
        <div class="scene-sun" /><span class="scene-star star-a">✳</span><span class="scene-star star-b">✦</span><span class="scene-star star-c">✧</span>
        <svg class="scene-car" viewBox="0 0 500 220" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M105 119L139 70C145 61 155 55 166 55H306C319 55 331 62 337 74L362 119L397 130C409 134 417 145 417 158V175H81V151C81 136 91 124 105 119Z" fill="#FFF8E4" stroke="#174A4B" stroke-width="7" stroke-linejoin="round"/>
          <path d="M153 73C156 68 161 65 167 65H223V111H126L153 73Z" fill="#9DE8DC" stroke="#174A4B" stroke-width="6" stroke-linejoin="round"/>
          <path d="M238 65H304C311 65 317 69 321 75L342 111H238V65Z" fill="#9DE8DC" stroke="#174A4B" stroke-width="6" stroke-linejoin="round"/>
          <path d="M83 148H414" stroke="#174A4B" stroke-width="7" stroke-linecap="round"/><path d="M91 131H113M383 131H409" stroke="#FF9A76" stroke-width="10" stroke-linecap="round"/>
          <circle cx="151" cy="173" r="27" fill="#173F40" stroke="#FFF8E4" stroke-width="8"/><circle cx="151" cy="173" r="9" fill="#FFE38A"/>
          <circle cx="348" cy="173" r="27" fill="#173F40" stroke="#FFF8E4" stroke-width="8"/><circle cx="348" cy="173" r="9" fill="#FFE38A"/>
          <path d="M201 139H276" stroke="#7FE0D4" stroke-width="7" stroke-linecap="round"/>
        </svg>
        <div class="scene-road"><span /><span /><span /></div>
        <div class="scene-badge"><v-icon icon="mdi-check" size="16" /> VAMOS CONTIGO</div>
      </div>
      <div class="brand-foot"><span>✳ &nbsp; Cuidamos cada detalle</span><span>01 — 05</span></div>
    </section>
    <section class="form-panel">
      <div class="form-content">
        <template v-if="mode === 'login'">
          <div class="form-overline"><span>ACCESO A TU CUENTA</span><v-icon icon="mdi-sparkles" size="16" /></div>
          <h2>Qué gusto verte</h2><p class="form-subtitle">Ingresa para volver a tu espacio del taller.</p>
          <v-form @submit.prevent="submit">
            <v-text-field v-model="email" label="Correo electrónico" type="email" autocomplete="email" :rules="[rules.required, rules.email]" prepend-inner-icon="mdi-email-outline" required />
            <v-text-field v-model="password" label="Contraseña" type="password" autocomplete="current-password" :rules="[rules.required]" prepend-inner-icon="mdi-lock-outline" required />
            <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
            <v-btn color="primary" type="submit" size="large" block :loading="loading">Iniciar sesión <v-icon end icon="mdi-arrow-right" /></v-btn>
          </v-form>
          <p class="auth-switch">¿Aún no tienes cuenta? <button type="button" @click="changeMode('register')">Crear cuenta</button></p>
          <p class="auth-switch"><button type="button" @click="router.push('/recuperar-contrasena')">¿Olvidaste tu contraseña?</button></p>
          <p class="secure-note"><v-icon icon="mdi-shield-check-outline" size="small" /> Tus datos viajan protegidos.</p>
        </template>
        <template v-else>
          <div class="form-overline"><span>UN BUEN SERVICIO EMPIEZA AQUÍ</span><v-icon icon="mdi-sparkles" size="16" /></div>
          <h2>Crear cuenta</h2><p class="form-subtitle">Registra tu perfil de cliente del taller.</p>
          <v-form @submit.prevent="submit">
            <v-text-field v-model="fullName" label="Nombre completo" autocomplete="name" :rules="[rules.required, rules.name]" prepend-inner-icon="mdi-account-outline" required />
            <v-text-field v-model="email" label="Correo electrónico" type="email" autocomplete="email" :rules="[rules.required, rules.email]" prepend-inner-icon="mdi-email-outline" required />
            <v-text-field v-model="phone" label="Teléfono (opcional)" autocomplete="tel" :rules="[rules.phone]" prepend-inner-icon="mdi-phone-outline" />
            <v-text-field v-model="password" label="Contraseña" type="password" autocomplete="new-password" :rules="[rules.required, rules.password]" hint="12 caracteres o más, mayúscula, minúscula, número y símbolo." persistent-hint prepend-inner-icon="mdi-lock-outline" required />
            <v-text-field v-model="confirmPassword" label="Confirmar contraseña" type="password" autocomplete="new-password" :rules="[rules.required, confirmationRule]" prepend-inner-icon="mdi-lock-check-outline" required />
            <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
            <v-btn color="primary" type="submit" size="large" block :loading="loading" class="mt-3">Crear cuenta <v-icon end icon="mdi-arrow-right" /></v-btn>
          </v-form>
          <p class="auth-switch">¿Ya tienes cuenta? <button type="button" @click="changeMode('login')">Iniciar sesión</button></p>
          <p class="secure-note"><v-icon icon="mdi-shield-check-outline" size="small" /> Contraseñas protegidas con BCrypt.</p>
        </template>
      </div>
    </section>
  </main>
</template>
