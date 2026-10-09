import { createApp } from 'vue'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import {
  VAlert, VApp, VAppBar, VAvatar, VBtn, VCard, VCardSubtitle, VCardText,
  VCardTitle, VChip, VCol, VContainer, VDialog, VForm, VIcon, VMain,
  VFileInput, VProgressLinear, VRow, VSelect, VSpacer, VTextField, VTable, VToolbarTitle,
} from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import App from './App.vue'
import router from './router'
import './style.css'

const vuetify = createVuetify({
  components: {
    VAlert, VApp, VAppBar, VAvatar, VBtn, VCard, VCardSubtitle, VCardText,
    VCardTitle, VChip, VCol, VContainer, VDialog, VForm, VIcon, VMain,
    VFileInput, VProgressLinear, VRow, VSelect, VSpacer, VTextField, VTable, VToolbarTitle,
  },
  directives,
  theme: { defaultTheme: 'taller', themes: { taller: { dark: false, colors: {
    primary: '#00C2CB', secondary: '#7FE0D4', accent: '#FFE38A', error: '#FF5D8F', warning: '#FF9A76', background: '#F4FAF9', surface: '#FFFFFF',
  } } } },
  icons: { defaultSet: 'mdi', aliases, sets: { mdi } },
})

createApp(App).use(router).use(vuetify).mount('#app')
