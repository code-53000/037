from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BoothZone, Booth, BoothStatus
from .serializers import BoothZoneSerializer, BoothSerializer
from .services import BoothAllocationService
from users.models import UserRole


class IsOrganizerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == UserRole.ORGANIZER


class BoothZoneViewSet(viewsets.ModelViewSet):
    queryset = BoothZone.objects.all().select_related('exhibition')
    serializer_class = BoothZoneSerializer
    permission_classes = [IsOrganizerOrReadOnly]
    filterset_fields = ['exhibition', 'zone_type']
    search_fields = ['name', 'exhibition__name']

    def get_queryset(self):
        qs = super().get_queryset()
        exhibition_id = self.request.query_params.get('exhibition_id')
        if exhibition_id:
            qs = qs.filter(exhibition_id=exhibition_id)
        return qs

    @action(detail=True, methods=['get'])
    def booth_map(self, request, pk=None):
        zone = self.get_object()
        data = BoothAllocationService.get_zone_booth_map(zone)
        return Response(data)


class BoothViewSet(viewsets.ModelViewSet):
    queryset = Booth.objects.all().select_related('zone', 'zone__exhibition')
    serializer_class = BoothSerializer
    permission_classes = [IsOrganizerOrReadOnly]
    filterset_fields = ['zone', 'zone__exhibition', 'status']
    search_fields = ['booth_code', 'zone__name']

    def get_queryset(self):
        qs = super().get_queryset()
        zone_id = self.request.query_params.get('zone_id')
        exhibition_id = self.request.query_params.get('exhibition_id')
        if zone_id:
            qs = qs.filter(zone_id=zone_id)
        if exhibition_id:
            qs = qs.filter(zone__exhibition_id=exhibition_id)
        return qs

    @action(detail=False, methods=['get'])
    def available(self, request):
        zone_id = request.query_params.get('zone_id')
        if not zone_id:
            return Response(
                {'detail': '请指定 zone_id 参数'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        zone = BoothZone.objects.get(pk=zone_id)
        booths = BoothAllocationService.get_available_booths(zone)
        serializer = self.get_serializer(booths, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def check_conflict(self, request, pk=None):
        booth = self.get_object()
        available, conflicts = BoothAllocationService.check_availability(booth)
        return Response({
            'available': available,
            'conflicts': conflicts,
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reserve(self, request, pk=None):
        if request.user.role != UserRole.ORGANIZER:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        booth = self.get_object()
        result = BoothAllocationService.reserve_booth(booth)
        http_status = status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST
        return Response({
            'success': result.success,
            'message': result.message,
            'conflicts': result.conflicts,
            'booth': self.get_serializer(result.booth).data if result.booth else None,
        }, status=http_status)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def release(self, request, pk=None):
        if request.user.role != UserRole.ORGANIZER:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        booth = self.get_object()
        result = BoothAllocationService.release_booth(booth)
        http_status = status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST
        return Response({
            'success': result.success,
            'message': result.message,
            'booth': self.get_serializer(result.booth).data if result.booth else None,
        }, status=http_status)
