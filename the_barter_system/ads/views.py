from rest_framework import viewsets, permissions, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ad, ExchangeProposal
from .serializers import AdSerializer, ExchangeProposalSerializer
from .permissions import IsOwnerOrReadOnly

from django.urls import reverse_lazy
from django.db.models import Q
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Ad, ExchangeProposal
from .forms import AdForm, ExchangeProposalForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.db import transaction


class AdPagination(PageNumberPagination):
    page_size = 10


class AdListView(ListView):
    model = Ad
    template_name = 'ads/ad_list.html'
    context_object_name = 'ads'
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        category = self.request.GET.get('category')
        condition = self.request.GET.get('condition')

        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q)
            )
        if category:
            qs = qs.filter(category=category)
        if condition:
            qs = qs.filter(condition=condition)

        return qs

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx.update({
            'q':         self.request.GET.get('q', ''),
            'category':  self.request.GET.get('category', ''),
            'condition': self.request.GET.get('condition', ''),
            'all_conditions': Ad.CONDITION_CHOICES,
            'all_categories': Ad.objects.values_list('category', flat=True).distinct(),
        })
        return ctx


class AdDetailView(DetailView):
    model = Ad
    template_name = 'ads/ad_detail.html'
    context_object_name = 'ad'


class AdCreateView(LoginRequiredMixin, CreateView):
    model = Ad
    form_class = AdForm
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ad_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Не удалось создать объявление. Пожалуйста, проверьте введённые данные.")
        return super().form_invalid(form)


class AdUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ad
    form_class = AdForm
    template_name = 'ads/ad_form.html'

    def test_func(self):
        return self.get_object().user == self.request.user

    def form_invalid(self, form):
        messages.error(
            self.request, "Не удалось обновить объявление. Проверьте форму.")
        return super().form_invalid(form)


class AdDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ad
    template_name = 'ads/ad_confirm_delete.html'
    success_url = reverse_lazy('ad_list')

    def test_func(self):
        return self.get_object().user == self.request.user


class AdViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly]
    pagination_class = AdPagination
    queryset = Ad.objects.all().order_by('-created_at')
    serializer_class = AdSerializer
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'condition', 'user']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProposalCreateView(LoginRequiredMixin, CreateView):
    model = ExchangeProposal
    form_class = ExchangeProposalForm
    template_name = 'ads/proposal_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.target_ad = get_object_or_404(Ad, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['target_ad'] = self.target_ad
        return kwargs

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx['target_ad'] = self.target_ad
        return ctx

    def form_valid(self, form):
        form.instance.ad_receiver = self.target_ad
        messages.success(
            self.request, "Предложение создано, ждём ответа получателя.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Не удалось создать предложение обмена. Проверьте форму.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('ad_detail', kwargs={'pk': self.target_ad.pk})


class ExchangeProposalViewSet(viewsets.ModelViewSet):
    queryset = ExchangeProposal.objects.all().order_by('-created_at')
    serializer_class = ExchangeProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'ad_sender', 'ad_receiver']
    ordering_fields = ['created_at']

    def get_target_ad(self):
        return get_object_or_404(Ad, pk=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save()


class ProposalListView(LoginRequiredMixin, ListView):
    model = ExchangeProposal
    template_name = 'ads/proposal_list.html'
    context_object_name = 'proposals'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset().select_related(
            'ad_sender__user', 'ad_receiver__user'
        ).order_by('-created_at')

        view_type = self.request.GET.get('type', 'all')
        if view_type == 'sent':
            qs = qs.filter(ad_sender__user=user)
        elif view_type == 'received':
            qs = qs.filter(ad_receiver__user=user)
        else:
            qs = qs.filter(
                Q(ad_sender__user=user) |
                Q(ad_receiver__user=user)
            )

        sender = self.request.GET.get('sender')
        receiver = self.request.GET.get('receiver')
        status = self.request.GET.get('status')
        if sender:
            qs = qs.filter(ad_sender__user__username=sender)
        if receiver:
            qs = qs.filter(ad_receiver__user__username=receiver)
        if status in dict(ExchangeProposal.STATUS_CHOICES):
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx.update({
            'view_type':     self.request.GET.get('type', 'all'),
            'sender':        self.request.GET.get('sender', ''),
            'receiver':      self.request.GET.get('receiver', ''),
            'status':        self.request.GET.get('status', ''),
            'status_choices': ExchangeProposal.STATUS_CHOICES,
        })
        return ctx


class ProposalDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ExchangeProposal
    template_name = 'ads/proposal_detail.html'
    context_object_name = 'proposal'

    def test_func(self):
        p = self.get_object()
        user = self.request.user
        return (p.ad_sender.user == user) or (p.ad_receiver.user == user)


def proposal_update_status(request, pk, action):
    proposal = get_object_or_404(ExchangeProposal, pk=pk)

    if proposal.ad_receiver.user != request.user:
        messages.error(request, "Только получатель может изменить статус.")
        return redirect('proposal_detail', pk=pk)

    if proposal.status != 'waiting':
        messages.info(request, "Статус уже был изменён ранее.")
        return redirect('proposal_detail', pk=pk)

    if action == 'accept':
        with transaction.atomic():
            sender_ad = proposal.ad_sender
            receiver_ad = proposal.ad_receiver
            owner_sender = sender_ad.user
            owner_receiver = receiver_ad.user
            sender_ad.user = owner_receiver
            receiver_ad.user = owner_sender

            sender_ad.save()
            receiver_ad.save()

            proposal.status = 'accepted'
            proposal.save()

        messages.success(
            request, "Обмен успешно выполнен — объявления поменялись владельцами.")

    elif action == 'reject':
        proposal.status = 'rejected'
        proposal.save()
        messages.success(request, "Предложение обмена отклонено.")

    else:
        messages.error(request, "Неверное действие.")

    return redirect('proposal_detail', pk=pk)


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect(request.GET.get('next', 'ad_list'))
        else:
            messages.error(request, "Неверное имя пользователя или пароль")
    else:
        form = AuthenticationForm(request)
    return render(request, 'registration/login.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect('ad_list')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('ad_list')
        else:
            messages.error(request, "Проверьте введённые данные")
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
