from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import CheckInGate, CheckIn, CheckInType, CheckInStatus
from .serializers import (
    CheckInGateSerializer,
    CheckInSerializer,
    CheckInVerifySerializer,
)
from users.models import UserRole


class CheckInGateViewSet(viewsets.ModelViewSet):
    queryset = CheckInGate.objects.all().select_related('exhibition')
    serializer_class = CheckInGateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['exhibition', 'gate_type', 'is_active']
    search_fields = ['name', 'location', 'exhibition__name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        exhibition_id = self.request.query_params.get('exhibition_id')
        if exhibition_id:
            qs = qs.filter(exhibition_id=exhibition_id)
        return qs


class CheckInViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CheckIn.objects.all().select_related(
        'exhibition', 'gate', 'operator',
    )
    serializer_class = CheckInSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['exhibition', 'gate', 'checkin_type', 'status', 'operator']
    search_fields = ['code_used', 'person_name', 'operator__username']
    ordering_fields = ['checkin_time']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_authenticated and user.role == UserRole.ORGANIZER):
            return qs.none()
        exhibition_id = self.request.query_params.get('exhibition_id')
        if exhibition_id:
            qs = qs.filter(exhibition_id=exhibition_id)
        today = self.request.query_params.get('today')
        if today and today.lower() == 'true':
            today_start = timezone.now().replace(hour=0, minute=0, second=0)
            qs = qs.filter(checkin_time__gte=today_start)
        return qs

    def get_serializer_class(self):
        if self.action == 'verify':
            return CheckInVerifySerializer
        return CheckInSerializer

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
        result_data = serializer.save()
        http_status = status.HTTP_200_OK if result_data['result']['status'] == CheckInStatus.SUCCESS else status.HTTP_400_BAD_REQUEST
        return Response(result_data, status=http_status)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        if request.user.role != UserRole.ORGANIZER:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        exhibition_id = request.query_params.get('exhibition_id')
        if not exhibition_id:
            return Response(
                {'detail': '请指定 exhibition_id 参数'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(exhibition_id=exhibition_id)

        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        today_qs = qs.filter(checkin_time__gte=today_start)

        total_count = qs.count()
        today_count = today_qs.count()
        success_count = qs.filter(status=CheckInStatus.SUCCESS).count()
        ticket_count = qs.filter(checkin_type=CheckInType.TICKET, status=CheckInStatus.SUCCESS).count()
        exhibitor_count = qs.filter(checkin_type=CheckInType.EXHIBITOR, status=CheckInStatus.SUCCESS).count()

        last_hour_start = timezone.now() - timedelta(hours=1)
        last_hour_count = qs.filter(checkin_time__gte=last_hour_start).count()

        hourly_stats = []
        now = timezone.now()
        for hour in range(24):
            hour_start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            count = qs.filter(checkin_time__gte=hour_start, checkin_time__lt=hour_end).count()
            hourly_stats.append({
                'hour': hour,
                'label': f'{hour:02d}:00',
                'count': count,
            })

        return Response({
            'exhibition_id': exhibition_id,
            'total': total_count,
            'today': today_count,
            'last_hour': last_hour_count,
            'success': success_count,
            'ticket_count': ticket_count,
            'exhibitor_count': exhibitor_count,
            'hourly': hourly_stats,
        })
