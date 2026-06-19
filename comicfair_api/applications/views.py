from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone

from .models import BoothApplication, ApplicationStatus
from .serializers import (
    BoothApplicationSerializer,
    BoothApplicationSubmitSerializer,
    ApplicationReviewSerializer,
    ApplicationPaySerializer,
    ApplicationCancelSerializer,
    ApplicationCheckInSerializer,
)
from users.models import UserRole


class IsExhibitorOrOrganizer(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == UserRole.ORGANIZER:
            return True
        if request.user.role == UserRole.EXHIBITOR:
            return view.action in [
                'list', 'retrieve', 'create', 'update',
                'partial_update', 'destroy', 'submit', 'cancel', 'my_applications',
            ]
        return view.action in ['list', 'retrieve']


class BoothApplicationViewSet(viewsets.ModelViewSet):
    queryset = BoothApplication.objects.all().select_related(
        'applicant', 'exhibition', 'preferred_zone', 'booth', 'booth__zone',
        'reviewed_by', 'checked_in_by',
    )
    serializer_class = BoothApplicationSerializer
    permission_classes = [IsExhibitorOrOrganizer]
    filterset_fields = [
        'exhibition', 'preferred_zone', 'status', 'applicant',
    ]
    search_fields = [
        'club_name', 'contact_name', 'contact_phone', 'applicant__username',
        'check_in_code',
    ]
    ordering_fields = ['created_at', 'submitted_at', 'reviewed_at', 'fee_amount']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_authenticated and user.role == UserRole.ORGANIZER):
            qs = qs.filter(applicant=user)
        club_name = self.request.query_params.get('club_name')
        if club_name:
            qs = qs.filter(club_name__icontains=club_name)
        return qs

    def perform_destroy(self, instance):
        if instance.status != ApplicationStatus.DRAFT:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有草稿状态的申请可以删除')
        instance.delete()

    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        qs = self.get_queryset().filter(applicant=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        instance = self.get_object()
        serializer = BoothApplicationSubmitSerializer(
            instance=instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance.status = ApplicationStatus.PENDING
        instance.submitted_at = timezone.now()
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def review(self, request, pk=None):
        if request.user.role != UserRole.ORGANIZER:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        instance = self.get_object()
        if instance.status != ApplicationStatus.PENDING:
            return Response(
                {'detail': '只有待审核状态的申请可以审核'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ApplicationReviewSerializer(
            instance=instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        instance = self.get_object()
        if request.user.role != UserRole.ORGANIZER and instance.applicant_id != request.user.id:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ApplicationPaySerializer(
            instance=instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        if request.user.role != UserRole.ORGANIZER and instance.applicant_id != request.user.id:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ApplicationCancelSerializer(
            instance=instance,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def check_in(self, request):
        if request.user.role != UserRole.ORGANIZER:
            return Response(
                {'detail': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ApplicationCheckInSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({
            'success': True,
            'message': '签到成功',
            'application': self.get_serializer(instance).data,
        })
