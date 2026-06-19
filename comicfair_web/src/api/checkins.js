import request from '@/utils/request'

export const getGateList = (params) => request.get('/checkins/gates/', { params })
export const createGate = (data) => request.post('/checkins/gates/', data)
export const updateGate = (id, data) => request.put(`/checkins/gates/${id}/`, data)

export const getCheckinRecords = (params) => request.get('/checkins/records/', { params })
export const verifyCheckin = (data) => request.post('/checkins/records/verify/', data)
export const getCheckinStats = (exhibitionId) =>
  request.get('/checkins/records/stats/', { params: { exhibition_id: exhibitionId } })
