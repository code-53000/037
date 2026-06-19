from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Exhibition, ExhibitionStatus
from .serializers import ExhibitionSerializer
from users.models import UserRole


class IsOrganizerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == UserRole.ORGANIZER


class ExhibitionViewSet(viewsets.ModelViewSet):
    queryset = Exhibition.objects.all()
    serializer_class = ExhibitionSerializer
    permission_classes = [IsOrganizerOrReadOnly]
    filterset_fields = ['status', 'start_date', 'end_date']
    search_fields = ['name', 'venue', 'subtitle']
    ordering_fields = ['start_date', 'end_date', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user.is_authenticated and self.request.user.role == UserRole.ORGANIZER):
            qs = qs.filter(status__in=[ExhibitionStatus.PUBLISHED, ExhibitionStatus.ONGOING])
        return qs

    @action(detail=False, methods=['get'])
    def active(self, request):
        qs = self.get_queryset().filter(status__in=[ExhibitionStatus.PUBLISHED, ExhibitionStatus.ONGOING])
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        exhibition = self.get_object()
        exhibition.status = ExhibitionStatus.PUBLISHED
        exhibition.save()
        return Response(self.get_serializer(exhibition).data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def stats(self, request, pk=None):
        exhibition = self.get_object()
        from booths.models import Booth, BoothZone
        from applications.models import BoothApplication, ApplicationStatus
        from tickets.models import Ticket
        from checkins.models import CheckIn

        zones = BoothZone.objects.filter(exhibition=exhibition)
        total_booths = Booth.objects.filter(zone__exhibition=exhibition).count()
        total_applications = BoothApplication.objects.filter(exhibition=exhibition).count()
        approved_applications = BoothApplication.objects.filter(
            exhibition=exhibition,
            status=ApplicationStatus.APPROVED,
        ).count()
        paid_applications = BoothApplication.objects.filter(
            exhibition=exhibition,
            status=ApplicationStatus.PAID,
        ).count()
        total_tickets = Ticket.objects.filter(exhibition=exhibition).count()
        total_checkins = CheckIn.objects.filter(exhibition=exhibition).count()

        zone_stats = []
        for zone in zones:
            zone_booths = Booth.objects.filter(zone=zone).count()
            zone_occupied = BoothApplication.objects.filter(
                exhibition=exhibition,
                booth__zone=zone,
                status__in=[ApplicationStatus.APPROVED, ApplicationStatus.PAID, ApplicationStatus.CHECKED_IN],
            ).count()
            zone_stats.append({
                'id': zone.id,
                'name': zone.name,
                'color': zone.color,
                'total_booths': zone_booths,
                'occupied': zone_occupied,
                'occupancy_rate': round(zone_occupied / zone_booths * 100, 2) if zone_booths > 0 else 0,
            })

        return Response({
            'exhibition': self.get_serializer(exhibition).data,
            'total_booths': total_booths,
            'total_applications': total_applications,
            'approved_applications': approved_applications,
            'paid_applications': paid_applications,
            'total_tickets': total_tickets,
            'total_checkins': total_checkins,
            'zone_stats': zone_stats,
        })
