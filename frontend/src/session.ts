import { computed, ref } from 'vue'
import type { User } from './api'

// Token sólo en memoria para que un XSS no pueda recuperarlo del almacenamiento web.
const token = ref<string | null>(null)
const user = ref<User | null>(null)
export const session = {
  token: computed(() => token.value), user: computed(() => user.value), isAuthenticated: computed(() => Boolean(token.value)),
  establish(accessToken: string, currentUser: User) { token.value = accessToken; user.value = currentUser },
  clear() { token.value = null; user.value = null },
}
