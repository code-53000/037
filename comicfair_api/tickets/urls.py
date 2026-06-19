from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketTierViewSet, TicketViewSet

router = DefaultRouter()
router.register(r'tiers', TicketTierViewSet, basename='tickettier')
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    path('', include(router.urls)),
]
