from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AdViewSet, ExchangeProposalViewSet,
    AdListView, AdDetailView,
    AdCreateView, AdUpdateView, AdDeleteView,
    ProposalCreateView, login, logout, signup,
    ProposalListView, ProposalDetailView, proposal_update_status
)

router = DefaultRouter()
router.register(r'ads', AdViewSet, basename='ad')
router.register(r'proposals', ExchangeProposalViewSet, basename='exchangeproposal')

urlpatterns = [
    path('api/', include(router.urls)),

    path('', AdListView.as_view(), name='ad_list'),
    path('ads/create/', AdCreateView.as_view(), name='ad_create'),
    path('ads/<int:pk>/', AdDetailView.as_view(), name='ad_detail'),
    path('ads/<int:pk>/edit/', AdUpdateView.as_view(), name='ad_update'),
    path('ads/<int:pk>/delete/', AdDeleteView.as_view(), name='ad_delete'),

    path('ads/<int:pk>/propose/', ProposalCreateView.as_view(), name='proposal_create'),    
    path('proposals/', ProposalListView.as_view(), name='proposal_list'),
    path('proposals/<int:pk>/', ProposalDetailView.as_view(), name='proposal_detail'),
    path('proposals/<int:pk>/<str:action>/', proposal_update_status, name='proposal_update_status'),


    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('signup/', signup, name='signup'),
]
