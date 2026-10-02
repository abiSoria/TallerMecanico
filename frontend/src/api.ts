const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'
export interface User { id: number; full_name: string; email: string; role: string }
export interface AuthResponse { access_token: string; token_type: string; expires_in: number; user: User }
export interface RegisterData { full_name: string; email: string; password: string; phone?: string }
export interface StaffUserData { full_name: string; email: string; password: string; role: 'administrador' | 'recepcionista' | 'asesor_servicio' | 'tecnico' }

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = body.detail
    const message = Array.isArray(detail) ? detail.map((item: { msg?: string }) => item.msg).join(' ') : detail
    throw new Error(message || `Error ${response.status}: no se pudo completar la solicitud`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  register: (data: RegisterData) => request<AuthResponse>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (email: string, password: string) => request<AuthResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: (token: string) => request<User>('/auth/me', {}, token),
  changePassword: (token: string, current_password: string, new_password: string) => request<void>('/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password, new_password }) }, token),
  staffUsers: (token: string) => request<User[]>('/admin/users', {}, token),
  createStaffUser: (token: string, data: StaffUserData) => request<User>('/admin/users', { method: 'POST', body: JSON.stringify(data) }, token),
}
