import request from '@/utils/request'

export const login = (data) => request.post('/auth/login/', data)
export const refreshToken = (data) => request.post('/auth/refresh/', data)
export const register = (data) => request.post('/auth/users/register/', data)
export const getCurrentUser = () => request.get('/auth/users/me/')
export const updateProfile = (data) => request.patch('/auth/users/update_profile/', data)
