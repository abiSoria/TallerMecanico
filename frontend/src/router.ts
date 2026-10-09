import { createRouter, createWebHistory } from 'vue-router'
import { session } from './session'
import AuthView from './views/AuthView.vue'
import DashboardView from './views/DashboardView.vue'
import PasswordRecoveryView from './views/PasswordRecoveryView.vue'
import RoleManagementView from './views/RoleManagementView.vue'
import WorkshopCreateView from './views/WorkshopCreateView.vue'
import WorkshopListView from './views/WorkshopListView.vue'

const router = createRouter({ history: createWebHistory(), scrollBehavior: () => ({ top: 0 }), routes: [
  { path: '/', redirect: '/ingresar' },
  { path: '/ingresar', component: AuthView, meta: { guestOnly: true } },
  { path: '/recuperar-contrasena', component: PasswordRecoveryView, meta: { guestOnly: true } },
  { path: '/restablecer-contrasena', component: PasswordRecoveryView, meta: { guestOnly: true } },
  { path: '/panel', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/admin/roles', component: RoleManagementView, meta: { requiresAuth: true, roles: ['administrador'] } },
  { path: '/talleres/alta', component: WorkshopCreateView, meta: { requiresAuth: true, roles: ['administrador', 'recepcionista'] } },
  { path: '/talleres', component: WorkshopListView, meta: { requiresAuth: true, roles: ['administrador', 'recepcionista'] } },
  { path: '/:pathMatch(.*)*', redirect: '/ingresar' },
] })

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !session.isAuthenticated.value) return '/ingresar'
  const allowedRoles = to.meta.roles as string[] | undefined
  if (allowedRoles && !allowedRoles.includes(session.user.value?.role ?? '')) return '/panel'
  if (to.meta.guestOnly && session.isAuthenticated.value) return '/panel'
})
export default router
