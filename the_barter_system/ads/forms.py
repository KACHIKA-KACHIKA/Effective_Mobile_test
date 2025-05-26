from django import forms
from django.core.exceptions import ValidationError
from .models import Ad, ExchangeProposal


class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ['title', 'description', 'image_url', 'category', 'condition']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
        }


class ExchangeProposalForm(forms.ModelForm):
    class Meta:
        model = ExchangeProposal
        fields = ['ad_sender', 'comment']
        widgets = {
            'ad_sender': forms.Select(attrs={'class': 'form-select'}),
            'comment':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, user=None, target_ad=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['ad_sender'].queryset = Ad.objects.filter(user=user)
        self.user = user
        self.target_ad = target_ad

    def clean_ad_sender(self):
        ad_sender = self.cleaned_data['ad_sender']
        if ad_sender.user != self.user:
            raise ValidationError("Вы можете предлагать только свои объявления.")
        if self.target_ad and ad_sender.pk == self.target_ad.pk:
            raise ValidationError("Нельзя обмениваться одним и тем же объявлением.")
        return ad_sender
