import request from '@/utils/request'

export const getApplicationList = (params) => request.get('/applications/', { params })
export const getMyApplications = (params) => request.get('/applications/my_applications/', { params })
export const getApplicationDetail = (id) => request.get(`/applications/${id}/`)
export const createApplication = (data) => request.post('/applications/', data)
export const updateApplication = (id, data) => request.patch(`/applications/${id}/`, data)
export const deleteApplication = (id) => request.delete(`/applications/${id}/`)
export const submitApplication = (id) => request.post(`/applications/${id}/submit/`)
export const reviewApplication = (id, data) => request.post(`/applications/${id}/review/`, data)
export const payApplication = (id, data) => request.post(`/applications/${id}/pay/`, data)
export const cancelApplication = (id, data) => request.post(`/applications/${id}/cancel/`, data)
export const checkinApplication = (data) => request.post('/applications/check_in/', data)
