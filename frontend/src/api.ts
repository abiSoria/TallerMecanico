const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'
export interface User { id: number; full_name: string; email: string; role: string; role_name: string }
export interface AuthResponse { access_token: string; token_type: string; expires_in: number; user: User }
export interface RegisterData { full_name: string; email: string; password: string; phone?: string }
export interface StaffUserData { full_name: string; email: string; password: string; role_id: number }
export interface RoleRecord { id: number; code: string; name: string; description: string | null; id_estatus: number; estatus: string; estatus_descripcion: string }
export interface PostalEntry { postal_code: string; neighborhood: string; municipality: string; state: string }
export interface WorkshopRecord {
  id: number; name: string; rfc: string; contact_email: string; street: string; number: string
  postal_code: string; state: string; municipality: string; neighborhood: string
  photo_filename: string; id_estatus: number; status: string; created_at: string
}
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
      headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
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
  roles: (token: string) => request<RoleRecord[]>('/admin/roles', {}, token),
  activeRoles: (token: string) => request<RoleRecord[]>('/admin/roles/active', {}, token),
  createRole: (token: string, data: { name: string; description: string }) => request<RoleRecord>('/admin/roles', { method: 'POST', body: JSON.stringify(data) }, token),
  updateRole: (token: string, id: number, data: { name: string; description: string }) => request<RoleRecord>(`/admin/roles/${id}`, { method: 'PUT', body: JSON.stringify(data) }, token),
  suspendRole: (token: string, id: number) => request<{ message: string }>(`/admin/roles/${id}`, { method: 'DELETE' }, token),
  postalByCode: (token: string, postalCode: string) => request<PostalEntry[]>(`/postal-codes/by-code/${encodeURIComponent(postalCode)}`, {}, token),
  postalReverse: (token: string, state: string, municipality: string, neighborhood: string) => request<PostalEntry[]>(`/postal-codes/search?${new URLSearchParams({ state, municipality, neighborhood })}`, {}, token),
  createWorkshop: (token: string, data: FormData) => request<{ id: number; name: string; rfc: string; message: string }>('/workshops', { method: 'POST', body: data }, token),
  workshops: (token: string) => request<WorkshopRecord[]>('/workshops', {}, token),
  workshopPhoto: async (token: string, id: number) => {
    let response: Response
    try { response = await fetch(`${API}/workshops/${id}/photo`, { headers: { Authorization: `Bearer ${token}` } }) }
    catch { throw new ApiError('No pudimos conectarnos con el servidor. Comprueba tu conexión e inténtalo de nuevo.') }
    if (!response.ok) throw new ApiError('No se pudo cargar la fotografía del taller.')
    return URL.createObjectURL(await response.blob())
  },
  registerClient: (token: string, data: ClientRegistrationData, confirmDuplicate = false) => request<{ code: string; message: string; data: ClientRegistrationData & { id: number; is_active: boolean }; duplicate_confirmed: boolean }>('/clients', { method: 'POST', body: JSON.stringify({ ...data, confirm_duplicate: confirmDuplicate }) }, token),
}
