import request from '@/utils/request'

export const getTicketTierList = (params) => request.get('/tickets/tiers/', { params })
export const getAvailableTiers = (exhibitionId) =>
  request.get('/tickets/tiers/available/', { params: { exhibition_id: exhibitionId } })
export const createTicketTier = (data) => request.post('/tickets/tiers/', data)
export const updateTicketTier = (id, data) => request.put(`/tickets/tiers/${id}/`, data)

export const getTicketList = (params) => request.get('/tickets/tickets/', { params })
export const getMyTickets = (params) => request.get('/tickets/tickets/my_tickets/', { params })
export const getTicketDetail = (id) => request.get(`/tickets/tickets/${id}/`)
export const purchaseTickets = (data) => request.post('/tickets/tickets/purchase/', data)
export const verifyTicket = (data) => request.post('/tickets/tickets/verify/', data)
export const refundTicket = (id, data) => request.post(`/tickets/tickets/${id}/refund/`, data)
