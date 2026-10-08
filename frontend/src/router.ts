import { createRouter, createWebHistory } from 'vue-router'
import { session } from './session'
import AuthView from './views/AuthView.vue'
import DashboardView from './views/DashboardView.vue'
import PasswordRecoveryView from './views/PasswordRecoveryView.vue'

const router = createRouter({ history: createWebHistory(), scrollBehavior: () => ({ top: 0 }), routes: [
  { path: '/', redirect: '/ingresar' },
  { path: '/ingresar', component: AuthView, meta: { guestOnly: true } },
  { path: '/recuperar-contrasena', component: PasswordRecoveryView, meta: { guestOnly: true } },
  { path: '/restablecer-contrasena', component: PasswordRecoveryView, meta: { guestOnly: true } },
  { path: '/panel', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/ingresar' },
] })

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !session.isAuthenticated.value) return '/ingresar'
  if (to.meta.guestOnly && session.isAuthenticated.value) return '/panel'
})
export default router
