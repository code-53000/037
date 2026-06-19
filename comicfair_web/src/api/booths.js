import request from '@/utils/request'

export const getZoneList = (params) => request.get('/booths/zones/', { params })
export const getZoneDetail = (id) => request.get(`/booths/zones/${id}/`)
export const getZoneBoothMap = (id) => request.get(`/booths/zones/${id}/booth_map/`)
export const createZone = (data) => request.post('/booths/zones/', data)
export const updateZone = (id, data) => request.put(`/booths/zones/${id}/`, data)

export const getBoothList = (params) => request.get('/booths/booths/', { params })
export const getBoothDetail = (id) => request.get(`/booths/booths/${id}/`)
export const getAvailableBooths = (zoneId) =>
  request.get('/booths/booths/available/', { params: { zone_id: zoneId } })
export const checkBoothConflict = (id) => request.get(`/booths/booths/${id}/check_conflict/`)
export const reserveBooth = (id) => request.post(`/booths/booths/${id}/reserve/`)
export const releaseBooth = (id) => request.post(`/booths/booths/${id}/release/`)
export const createBooth = (data) => request.post('/booths/booths/', data)
export const updateBooth = (id, data) => request.put(`/booths/booths/${id}/`, data)
