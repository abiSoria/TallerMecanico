<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError, api, type ClientRegistrationAudit, type ClientRegistrationData, type StaffUserData, type User } from '../api'
import { session } from '../session'
import { emailRule, nameRule, passwordRule } from '../validation'

const router = useRouter()
const role = computed(() => session.user.value?.role ?? 'cliente')
const greeting = computed(() => session.user.value?.full_name?.trim().split(/\s+/)[0] ?? 'equipo')
const profile = computed(() => profiles[role.value] ?? profiles.cliente)
const token = session.token.value!
const passwordDialog = ref(false)
const staffDialog = ref(false)
const clientDialog = ref(false)
const duplicateDialog = ref(false)
const busy = ref(false)
const error = ref('')
const message = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const staff = ref<User[]>([])
const clientRegistrations = ref<ClientRegistrationAudit[]>([])
const clientRegistrationsLoading = ref(false)
const clientRegistrationsError = ref('')
const duplicateClientId = ref<number | undefined>()
const emptyClient = (): ClientRegistrationData => ({ full_name: '', street: '', number: '', neighborhood: '', municipality: '', state: '', primary_phone: '', alternate_phone: '', email: '' })
const newClient = ref<ClientRegistrationData>(emptyClient())
const staffLoading = ref(false)
const newStaff = ref({ full_name: '', email: '', password: '', role: 'recepcionista' as StaffUserData['role'] })
const allowedStaffRoles: Array<{ title: string; value: StaffUserData['role'] }> = [
  { title: 'Administrador', value: 'administrador' },
  { title: 'Recepcionista', value: 'recepcionista' },
  { title: 'Asesor de servicio', value: 'asesor_servicio' },
  { title: 'Técnico', value: 'tecnico' },
]
const roleNames: Record<string, string> = {
  administrador: 'Administrador', recepcionista: 'Recepcionista', asesor_servicio: 'Asesor de servicio',
  tecnico: 'Técnico', cliente: 'Cliente', sistema: 'Sistema',
}
const roleColors: Record<string, string> = {
  administrador: 'primary', recepcionista: 'warning', asesor_servicio: 'secondary',
  tecnico: 'error', cliente: 'primary', sistema: 'grey',
}
const confirmationRule = (value: string) => value === newPassword.value || 'Las contraseñas no coinciden.'
const staffPasswordRule = (value: string) => passwordRule(value)
const requiredClientData = (value: string) => Boolean(value?.trim()) || 'Campo obligatorio.'
const clientPhoneRule = (value: string) => /^(?=(?:\D*\d){7,})[+0-9() -]{7,20}$/.test(value.trim()) || 'Ingresa un teléfono válido.'

function openClientDialog() { error.value = ''; newClient.value = emptyClient(); clientDialog.value = true }
function closeClientDialog() { clientDialog.value = false; duplicateDialog.value = false; error.value = '' }

async function saveClient(confirmDuplicate = false) {
  busy.value = true; error.value = ''
  try {
    const result = await api.registerClient(token, newClient.value, confirmDuplicate)
    message.value = result.message
    closeClientDialog()
    newClient.value = emptyClient()
    if (role.value === 'administrador') await loadClientRegistrations()
  } catch (err) {
    if (err instanceof ApiError && err.code === 'POSSIBLE_DUPLICATE') {
      duplicateClientId.value = err.possibleClientId
      duplicateDialog.value = true
    } else error.value = err instanceof Error ? err.message : 'No se pudo registrar el cliente.'
  } finally { busy.value = false }
}

const profiles: Record<string, { eyebrow: string; title: string; description: string; icon: string; sticker: string; tone: string; modules: Array<{ title: string; caption: string; icon: string; color: string; tag: string }> }> = {
  administrador: {
    eyebrow: 'CENTRO DE MANDO', title: 'Todo el taller, de un vistazo.', description: 'Coordina el equipo y mantén el trabajo avanzando. Hoy es un buen día para dejarlo todo afinado.', icon: 'mdi-view-dashboard-variant', sticker: 'PIT CREW', tone: 'mint',
    modules: [
      { title: 'Equipo y accesos', caption: 'Crea cuentas y asigna perfiles al personal.', icon: 'mdi-account-multiple-plus', color: 'teal', tag: 'GESTIÓN' },
      { title: 'Clientes', caption: 'Registra nuevos clientes del taller.', icon: 'mdi-account-plus', color: 'coral', tag: 'CLIENTES' },
      { title: 'Órdenes activas', caption: 'Revisa el trabajo en curso.', icon: 'mdi-clipboard-text-clock', color: 'yellow', tag: 'OPERACIÓN' },
    ],
  },
  recepcionista: {
    eyebrow: 'RECEPCIÓN', title: 'La primera parada del taller.', description: 'Recibe cada vehículo con una sonrisa y deja todo listo para que el equipo se ponga en marcha.', icon: 'mdi-door-open', sticker: 'HOLA, EQUIPO', tone: 'peach',
    modules: [
      { title: 'Clientes', caption: 'Registra nuevos clientes del taller.', icon: 'mdi-account-plus', color: 'teal', tag: 'RECEPCIÓN' },
      { title: 'Vehículos', caption: 'Próximamente: alta y ficha del vehículo.', icon: 'mdi-car-side', color: 'coral', tag: 'INVENTARIO' },
      { title: 'Nueva orden', caption: 'Próximamente: recepción de una reparación.', icon: 'mdi-clipboard-plus', color: 'yellow', tag: 'ÓRDENES' },
    ],
  },
  asesor_servicio: {
    eyebrow: 'ASESORÍA DE SERVICIO', title: 'Cada reparación, bien acompañada.', description: 'Mantén a cada cliente al tanto y convierte el seguimiento en una gran experiencia.', icon: 'mdi-headset', sticker: 'EN CONTACTO', tone: 'lavender',
    modules: [
      { title: 'Seguimiento', caption: 'Próximamente: avance de órdenes del taller.', icon: 'mdi-progress-check', color: 'teal', tag: 'ESTADO' },
      { title: 'Autorizaciones', caption: 'Próximamente: aprobaciones de clientes.', icon: 'mdi-check-decagram', color: 'coral', tag: 'CLIENTES' },
      { title: 'Notificaciones', caption: 'Próximamente: mensajes de actualización.', icon: 'mdi-message-badge', color: 'yellow', tag: 'AVISOS' },
    ],
  },
  tecnico: {
    eyebrow: 'BAHÍA DE SERVICIO', title: 'Manos expertas. Grandes resultados.', description: 'Aquí empieza el trabajo bien hecho. Documenta hallazgos y lleva cada auto un paso más cerca del camino.', icon: 'mdi-wrench-cog', sticker: 'EN EL TALLER', tone: 'blue',
    modules: [
      { title: 'Diagnósticos', caption: 'Próximamente: hallazgos y notas técnicas.', icon: 'mdi-magnify-scan', color: 'teal', tag: 'DIAGNÓSTICO' },
      { title: 'Reparaciones', caption: 'Próximamente: actualización de avances.', icon: 'mdi-engine-outline', color: 'coral', tag: 'TRABAJO' },
      { title: 'Refacciones', caption: 'Próximamente: piezas y disponibilidad.', icon: 'mdi-cog-transfer', color: 'yellow', tag: 'ALMACÉN' },
    ],
  },
  cliente: {
    eyebrow: 'TU ESPACIO EN EL TALLER', title: 'Tu auto está en buenas manos.', description: 'Muy pronto podrás ver cada actualización de su visita aquí. Gracias por confiar en nuestro equipo.', icon: 'mdi-car-connected', sticker: 'TODO EN ORDEN', tone: 'mint',
    modules: [
      { title: 'Mis vehículos', caption: 'Próximamente: tu garaje y datos de tus autos.', icon: 'mdi-car-multiple', color: 'teal', tag: 'MI GARAJE' },
      { title: 'Mis reparaciones', caption: 'Próximamente: estado e historial de servicio.', icon: 'mdi-clipboard-check', color: 'coral', tag: 'SEGUIMIENTO' },
      { title: 'Avisos del taller', caption: 'Próximamente: novedades en tiempo real.', icon: 'mdi-bell-ring', color: 'yellow', tag: 'NOVEDADES' },
    ],
  },
  sistema: {
    eyebrow: 'PROCESOS INTERNOS', title: 'Operación automatizada.', description: 'Esta identidad técnica se reserva para procesos internos y no se administra como cuenta de usuario.', icon: 'mdi-cog-sync', sticker: 'AUTOMATIZACIÓN', tone: 'blue',
    modules: [{ title: 'Auditoría', caption: 'Eventos registrados para trazabilidad.', icon: 'mdi-shield-search', color: 'teal', tag: 'SISTEMA' }],
  },
}

async function loadStaff() {
  if (role.value !== 'administrador') return
  staffLoading.value = true
  try { staff.value = await api.staffUsers(token) }
  catch (err) { error.value = err instanceof Error ? err.message : 'No se pudo cargar el equipo.' }
  finally { staffLoading.value = false }
}

async function loadClientRegistrations() {
  if (role.value !== 'administrador') return
  clientRegistrationsLoading.value = true
  clientRegistrationsError.value = ''
  try { clientRegistrations.value = await api.clientRegistrations(token) }
  catch (err) { clientRegistrationsError.value = err instanceof Error ? err.message : 'No se pudo cargar el registro de clientes.' }
  finally { clientRegistrationsLoading.value = false }
}

function formatRegistrationDate(value: string) {
  return new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

async function createStaffAccount() {
  busy.value = true; error.value = ''; message.value = ''
  try {
    await api.createStaffUser(token, { ...newStaff.value, full_name: newStaff.value.full_name.trim(), email: newStaff.value.email.trim().toLowerCase() })
    message.value = `Cuenta creada para ${newStaff.value.full_name}. Ya puede iniciar sesión con el perfil ${roleNames[newStaff.value.role]}.`
    staffDialog.value = false
    newStaff.value = { full_name: '', email: '', password: '', role: 'recepcionista' }
    await loadStaff()
  } catch (err) { error.value = err instanceof Error ? err.message : 'No se pudo crear la cuenta.' }
  finally { busy.value = false }
}

async function updatePassword() {
  busy.value = true; error.value = ''
  try {
    await api.changePassword(token, currentPassword.value, newPassword.value)
    message.value = 'Contraseña actualizada. Inicia sesión de nuevo con tu nueva clave.'
    passwordDialog.value = false
    session.clear()
    await router.push('/ingresar')
  } catch (err) { error.value = err instanceof Error ? err.message : 'No se pudo cambiar la contraseña.' }
  finally { busy.value = false }
}

function logout() { session.clear(); void router.push('/ingresar') }
function closeStaffDialog() { staffDialog.value = false; error.value = '' }
onMounted(() => { void loadStaff(); void loadClientRegistrations() })
</script>

<template>
  <div class="garage-app">
    <v-app-bar class="garage-appbar" flat>
      <div class="brand-mini"><span class="brand-mini-icon"><v-icon icon="mdi-wrench-clock" /></span><span>pit<span class="brand-mini-dot">.</span>stop</span></div>
      <v-spacer />
      <v-chip class="profile-chip mr-3" :color="roleColors[role]" variant="tonal" size="small"><v-icon start icon="mdi-account-circle-outline" />{{ roleNames[role] ?? role }}</v-chip>
      <v-btn icon="mdi-lock-reset" aria-label="Cambiar contraseña" variant="text" @click="passwordDialog = true" />
      <v-btn icon="mdi-logout-variant" aria-label="Cerrar sesión" variant="text" class="mr-2" @click="logout" />
    </v-app-bar>

    <v-main>
      <v-container class="garage-page py-7 py-md-10">
        <v-alert v-if="message" type="success" variant="tonal" closable class="mb-6" @click:close="message = ''">{{ message }}</v-alert>
        <v-alert v-if="error && !staffDialog && !passwordDialog" type="error" variant="tonal" closable class="mb-6" @click:close="error = ''">{{ error }}</v-alert>

        <section class="hero-card" :class="`hero-${profile.tone}`">
          <div class="hero-copy">
            <div class="hero-eyebrow"><span class="eyebrow-sparkle">✳</span>{{ profile.eyebrow }}</div>
            <h1>{{ profile.title }}</h1>
            <p class="hero-description">{{ profile.description }}</p>
            <div class="hero-welcome"><span class="welcome-dot" />¡Qué gusto verte, {{ greeting }}!</div>
          </div>
          <div class="hero-art" aria-hidden="true">
            <div class="sun-disc" />
            <div class="art-spark spark-one">✳</div><div class="art-spark spark-two">✦</div><div class="art-spark spark-three">✧</div>
            <div class="art-car"><div class="car-roof" /><div class="car-body"><span class="car-window" /><span class="car-grille" /><span class="car-light" /></div><div class="car-wheel wheel-left" /><div class="car-wheel wheel-right" /></div>
            <div class="art-tool"><v-icon :icon="profile.icon" /></div>
            <div class="art-sticker">{{ profile.sticker }}</div>
            <div class="art-ground" />
          </div>
          <div class="hero-confetti confetti-a" /><div class="hero-confetti confetti-b" /><div class="hero-confetti confetti-c" />
        </section>

        <div class="section-heading mt-9 mb-4">
          <div><div class="section-kicker">TU TABLERO</div><h2>¿Qué vamos a poner en marcha?</h2></div>
          <v-btn v-if="role === 'administrador'" color="primary" rounded="lg" prepend-icon="mdi-account-plus" class="text-none" @click="staffDialog = true">Agregar al equipo</v-btn>
        </div>

        <div v-if="role === 'administrador' || role === 'recepcionista'" class="d-flex justify-end mb-4">
          <v-btn color="primary" rounded="lg" prepend-icon="mdi-account-plus" class="text-none" @click="openClientDialog">Registrar cliente</v-btn>
        </div>

        <v-row class="module-grid">
          <v-col v-for="(module, index) in profile.modules" :key="module.title" cols="12" sm="6" md="4">
            <v-card class="module-card h-100" :style="{ '--card-delay': `${index * 80}ms` }" rounded="xl" elevation="0">
              <div class="module-card-top"><span class="module-icon" :class="`icon-${module.color}`"><v-icon :icon="module.icon" size="25" /></span><span class="module-tag">{{ module.tag }}</span></div>
              <h3>{{ module.title }}</h3><p>{{ module.caption }}</p>
              <div class="module-card-bottom"><span v-if="module.title !== 'Clientes' || (role !== 'administrador' && role !== 'recepcionista')" class="coming-soon"><i />EN PREPARACIÓN</span><span v-else class="coming-soon">DISPONIBLE</span><v-icon icon="mdi-arrow-up-right" size="18" class="module-arrow" /></div>
            </v-card>
          </v-col>
        </v-row>

        <v-card v-if="role === 'administrador'" class="team-card mt-7" rounded="xl" elevation="0">
          <div class="team-heading"><div><div class="section-kicker">TU PIT CREW</div><h2>Accesos del equipo</h2><p>Un perfil por persona, con permisos a la medida de su trabajo.</p></div><v-avatar color="secondary" size="52"><v-icon icon="mdi-account-group" color="teal-darken-3" /></v-avatar></div>
          <v-progress-linear v-if="staffLoading" indeterminate color="primary" />
          <div v-else-if="staff.length" class="team-list">
            <div v-for="member in staff" :key="member.id" class="team-row"><v-avatar color="primary" variant="tonal" size="40"><span class="avatar-initial">{{ member.full_name.slice(0, 1).toUpperCase() }}</span></v-avatar><div class="team-member"><strong>{{ member.full_name }}</strong><span>{{ member.email }}</span></div><v-chip :color="roleColors[member.role]" variant="tonal" size="small">{{ roleNames[member.role] ?? member.role }}</v-chip></div>
          </div>
          <div v-else class="empty-team"><v-icon icon="mdi-account-multiple-outline" size="32" /><p>Aún no hay cuentas internas. Invita a tu equipo para que cada quien entre con su propio perfil.</p><v-btn color="primary" variant="tonal" rounded="lg" prepend-icon="mdi-account-plus" class="text-none" @click="staffDialog = true">Crear primera cuenta</v-btn></div>
          <div class="team-footer"><v-icon icon="mdi-shield-check-outline" size="17" />El rol de sistema queda reservado para tareas automatizadas.</div>
        </v-card>

        <v-card v-if="role === 'administrador'" class="team-card mt-7" rounded="xl" elevation="0">
          <div class="team-heading"><div><div class="section-kicker">AUDITORÍA</div><h2>Registros</h2><p>Consulta quién registró cada cliente y cuándo.</p></div><v-avatar color="secondary" size="52"><v-icon icon="mdi-clipboard-text-clock-outline" color="teal-darken-3" /></v-avatar></div>
          <v-progress-linear v-if="clientRegistrationsLoading" indeterminate color="primary" />
          <v-alert v-else-if="clientRegistrationsError" type="error" variant="tonal" class="mt-4">{{ clientRegistrationsError }}</v-alert>
          <div v-else-if="clientRegistrations.length" class="registration-table-scroll">
            <table class="registration-table">
              <thead><tr><th>Cliente</th><th>Lo agregó</th><th>Fecha y hora</th></tr></thead>
              <tbody><tr v-for="(entry, index) in clientRegistrations" :key="`${entry.registered_at}-${index}`"><td>{{ entry.client_name }}</td><td>{{ entry.registered_by }}</td><td>{{ formatRegistrationDate(entry.registered_at) }}</td></tr></tbody>
            </table>
          </div>
          <div v-else class="empty-team"><v-icon icon="mdi-clipboard-text-clock-outline" size="32" /><p>Aún no hay clientes registrados.</p></div>
        </v-card>

        <footer class="garage-footer"><span>HECHO CON CUIDADO EN EL TALLER</span><span>✳ &nbsp; Kilómetro a kilómetro.</span></footer>
      </v-container>
    </v-main>

    <v-dialog v-model="clientDialog" max-width="760">
      <v-card class="dialog-card" rounded="xl">
        <v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-account-plus" /></span><span>Registrar cliente</span></v-card-title>
        <v-card-subtitle>Captura los datos del cliente para el taller.</v-card-subtitle>
        <v-card-text class="pt-5">
          <v-form @submit.prevent="saveClient()">
            <v-row dense>
              <v-col cols="12"><v-text-field v-model="newClient.full_name" label="Nombre completo" :rules="[requiredClientData]" required /></v-col>
              <v-col cols="12" sm="8"><v-text-field v-model="newClient.street" label="Calle" :rules="[requiredClientData]" required /></v-col>
              <v-col cols="12" sm="4"><v-text-field v-model="newClient.number" label="Número" :rules="[requiredClientData]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="newClient.neighborhood" label="Colonia" :rules="[requiredClientData]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="newClient.municipality" label="Municipio" :rules="[requiredClientData]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="newClient.state" label="Estado" :rules="[requiredClientData]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="newClient.primary_phone" label="Teléfono principal" type="tel" :rules="[requiredClientData, clientPhoneRule]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="newClient.alternate_phone" label="Teléfono alterno" type="tel" :rules="[requiredClientData, clientPhoneRule]" required /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="newClient.email" label="Correo electrónico" type="email" :rules="[requiredClientData, emailRule]" required /></v-col>
            </v-row>
            <v-alert v-if="error" type="error" variant="tonal" class="mt-3">{{ error }}</v-alert>
            <div class="dialog-actions mt-5"><v-btn variant="text" class="text-none" @click="closeClientDialog">Cancelar</v-btn><v-btn color="primary" type="submit" rounded="lg" class="text-none" :loading="busy">Guardar <v-icon end icon="mdi-arrow-right" /></v-btn></div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="duplicateDialog" max-width="480">
      <v-card class="dialog-card" rounded="xl"><v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-account-alert-outline" /></span><span>Posible cliente duplicado</span></v-card-title><v-card-text>Se encontró una coincidencia (cliente {{ duplicateClientId }}). ¿Confirmas que deseas continuar con el registro?</v-card-text><v-card-actions class="dialog-actions"><v-btn variant="text" class="text-none" @click="duplicateDialog = false">Revisar datos</v-btn><v-btn color="primary" rounded="lg" class="text-none" :loading="busy" @click="saveClient(true)">Confirmar registro</v-btn></v-card-actions></v-card>
    </v-dialog>

    <v-dialog v-model="staffDialog" max-width="520">
      <v-card class="dialog-card" rounded="xl"><v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-account-plus" /></span><span>Invitar al equipo</span></v-card-title><v-card-subtitle>Crearemos la cuenta con el rol adecuado para su trabajo.</v-card-subtitle>
        <v-card-text class="pt-5"><v-form @submit.prevent="createStaffAccount">
          <v-text-field v-model="newStaff.full_name" label="Nombre completo" autocomplete="name" :rules="[v => !!v || 'Campo obligatorio', nameRule]" prepend-inner-icon="mdi-account-outline" required />
          <v-text-field v-model="newStaff.email" label="Correo de acceso" autocomplete="email" type="email" :rules="[v => !!v || 'Campo obligatorio', emailRule]" prepend-inner-icon="mdi-email-outline" required />
          <v-select v-model="newStaff.role" label="Perfil del equipo" :items="allowedStaffRoles" item-title="title" item-value="value" prepend-inner-icon="mdi-badge-account-outline" />
          <v-text-field v-model="newStaff.password" label="Contraseña temporal" type="password" autocomplete="new-password" :rules="[staffPasswordRule]" hint="12+ caracteres, mayúscula, minúscula, número y símbolo." persistent-hint prepend-inner-icon="mdi-lock-outline" required />
          <v-alert v-if="error" type="error" variant="tonal" class="mt-4">{{ error }}</v-alert>
          <div class="dialog-actions mt-5"><v-btn variant="text" class="text-none" @click="closeStaffDialog">Cancelar</v-btn><v-btn color="primary" type="submit" rounded="lg" class="text-none" :loading="busy">Crear cuenta <v-icon end icon="mdi-arrow-right" /></v-btn></div>
        </v-form></v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="passwordDialog" max-width="480"><v-card class="dialog-card" rounded="xl"><v-card-title class="dialog-title"><span class="dialog-icon"><v-icon icon="mdi-lock-reset" /></span><span>Cambiar contraseña</span></v-card-title><v-card-text><v-form @submit.prevent="updatePassword"><v-text-field v-model="currentPassword" label="Contraseña actual" type="password" autocomplete="current-password" :rules="[v => !!v || 'Campo obligatorio']" required /><v-text-field v-model="newPassword" label="Nueva contraseña" type="password" autocomplete="new-password" :rules="[passwordRule]" required /><v-text-field v-model="confirmPassword" label="Confirmar contraseña" type="password" autocomplete="new-password" :rules="[confirmationRule]" required /><v-alert v-if="error" type="error" variant="tonal" class="mb-3">{{ error }}</v-alert><div class="dialog-actions"><v-btn variant="text" class="text-none" @click="passwordDialog = false">Cancelar</v-btn><v-btn color="primary" type="submit" rounded="lg" class="text-none" :loading="busy">Actualizar</v-btn></div></v-form></v-card-text></v-card></v-dialog>
  </div>
</template>
