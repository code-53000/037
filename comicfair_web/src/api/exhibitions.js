import request from '@/utils/request'

export const getExhibitionList = (params) => request.get('/exhibitions/', { params })
export const getActiveExhibitions = () => request.get('/exhibitions/active/')
export const getExhibitionDetail = (id) => request.get(`/exhibitions/${id}/`)
export const getExhibitionStats = (id) => request.get(`/exhibitions/${id}/stats/`)
export const createExhibition = (data) => request.post('/exhibitions/', data)
export const updateExhibition = (id, data) => request.put(`/exhibitions/${id}/`, data)
export const publishExhibition = (id) => request.post(`/exhibitions/${id}/publish/`)
