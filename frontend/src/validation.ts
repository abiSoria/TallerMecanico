// Reglas duplicadas en RegisterIn y ChangePasswordIn del servidor.
export const emailRule = (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value) || 'Ingresa un correo válido.'
export const nameRule = (value: string) => (value.trim().length >= 2 && value.trim().length <= 120 && /^[\p{L}\p{M}\w .'-]+$/u.test(value.trim())) || 'Escribe un nombre válido de 2 a 120 caracteres.'
export const phoneRule = (value: string) => !value || /^[+\d() -]{7,20}$/.test(value.trim()) || 'Ingresa un teléfono válido.'
export const passwordRule = (value: string) => (new TextEncoder().encode(value).length <= 72 && /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d\s])\S{12,72}$/.test(value)) || 'Usa 12–72 caracteres con mayúscula, minúscula, número y símbolo, sin espacios.'
