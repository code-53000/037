from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TicketTier, Ticket, TicketStatus
from .serializers import (
    TicketTierSerializer,
    TicketSerializer,
    TicketPurchaseSerializer,
    TicketVerifySerializer,
    TicketRefundSerializer,
)
from users.models import UserRole


class TicketTierViewSet(viewsets.ModelViewSet):
    queryset = TicketTier.objects.all().select_related('exhibition')
    serializer_class = TicketTierSerializer
    filterset_fields = ['exhibition', 'ticket_type', 'on_sale']
    search_fields = ['name', 'exhibition__name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'available']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user.is_authenticated and self.request.user.role == UserRole.ORGANIZER):
            qs = qs.filter(on_sale=True)
        return qs

    @action(detail=False, methods=['get'])
    def available(self, request):
        exhibition_id = request.query_params.get('exhibition_id')
        qs = self.get_queryset().filter(on_sale=True)
        if exhibition_id:
            qs = qs.filter(exhibition_id=exhibition_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().select_related(
        'user', 'exhibition', 'tier',
    )
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['exhibition', 'tier', 'ticket_type', 'status', 'user']
    search_fields = ['ticket_no', 'ticket_code', 'holder_name', 'holder_phone', 'user__username']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_authenticated and user.role == UserRole.ORGANIZER):
            qs = qs.filter(user=user)
        return qs

    def get_serializer_class(self):
        if self.action == 'purchase':
            return TicketPurchaseSerializer
        if self.action == 'verify':
            return TicketVerifySerializer
        if self.action == 'refund':
            return TicketRefundSerializer
        return TicketSerializer

    def create(self, request, *args, **kwargs):
        return Response(
            {'detail': '请使用 /purchase/ 接口购票'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=['get'])
    def my_tickets(self, request):
        qs = self.get_queryset().filter(user=request.user)
        exhibition_id = request.query_params.get('exhibition_id')
        if exhibition_id:
            qs = qs.filter(exhibition_id=exhibition_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def purchase(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        tickets = serializer.save()
        return Response(
            {
                'success': True,
                'message': f'成功购买 {len(tickets)} 张票',
                'tickets': TicketSerializer(tickets, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def verify(self, request):
        if request.user.role != UserRole.ORGANIZER:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response({
            'success': True,
            'message': '验票成功',
            'ticket': TicketSerializer(ticket).data,
        })

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        ticket = self.get_object()
        if request.user.role != UserRole.ORGANIZER and ticket.user_id != request.user.id:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(
            instance=ticket,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response({
            'success': True,
            'message': '退票成功',
            'ticket': TicketSerializer(ticket).data,
        })
