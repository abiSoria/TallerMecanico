const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'
export interface User { id: number; full_name: string; email: string; role: string }
export interface AuthResponse { access_token: string; token_type: string; expires_in: number; user: User }
export interface RegisterData { full_name: string; email: string; password: string; phone?: string }
export interface StaffUserData { full_name: string; email: string; password: string; role: 'administrador' | 'recepcionista' | 'asesor_servicio' | 'tecnico' }
export interface ClientRegistrationData {
  full_name: string; street: string; number: string; neighborhood: string; municipality: string; state: string
  primary_phone: string; alternate_phone: string; email: string
}
export interface ClientRegistrationAudit { client_name: string; registered_by: string; registered_at: string }
export class ApiError extends Error {
  constructor(message: string, readonly code?: string, readonly possibleClientId?: number) { super(message) }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
    })
  } catch {
    throw new ApiError('No pudimos conectarnos con el servidor. Comprueba tu conexión e inténtalo de nuevo.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = body.detail
    const message = Array.isArray(detail) ? detail.map((item: { msg?: string }) => item.msg).join(' ') : typeof detail === 'object' && detail !== null ? detail.message : detail
    const friendlyMessage = ['RECOVERY_NOT_CONFIGURED', 'PERSISTENCE_ERROR'].includes(detail?.code) && message
      ? message
      : response.status >= 500
      ? 'Ocurrió un problema en el servidor. Inténtalo de nuevo más tarde.'
      : message || 'No pudimos completar la solicitud. Revisa los datos e inténtalo de nuevo.'
    throw new ApiError(friendlyMessage, detail?.code, detail?.possible_client_id)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  register: (data: RegisterData) => request<AuthResponse>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (email: string, password: string) => request<AuthResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  requestPasswordReset: (email: string) => request<{ code: string; message: string }>('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }),
  resetPassword: (token: string, new_password: string) => request<void>('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, new_password }) }),
  me: (token: string) => request<User>('/auth/me', {}, token),
  changePassword: (token: string, current_password: string, new_password: string) => request<void>('/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password, new_password }) }, token),
  staffUsers: (token: string) => request<User[]>('/admin/users', {}, token),
  clientRegistrations: (token: string) => request<ClientRegistrationAudit[]>('/admin/client-registrations', {}, token),
  createStaffUser: (token: string, data: StaffUserData) => request<User>('/admin/users', { method: 'POST', body: JSON.stringify(data) }, token),
  registerClient: (token: string, data: ClientRegistrationData, confirmDuplicate = false) => request<{ code: string; message: string; data: ClientRegistrationData & { id: number; is_active: boolean }; duplicate_confirmed: boolean }>('/clients', { method: 'POST', body: JSON.stringify({ ...data, confirm_duplicate: confirmDuplicate }) }, token),
}
