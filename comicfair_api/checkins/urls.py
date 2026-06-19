from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CheckInGateViewSet, CheckInViewSet

router = DefaultRouter()
router.register(r'gates', CheckInGateViewSet, basename='checkingate')
router.register(r'records', CheckInViewSet, basename='checkin')

urlpatterns = [
    path('', include(router.urls)),
]
