from rest_framework import serializers
from .models import Ad, ExchangeProposal

class AdSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Ad
        fields = ['id', 'user', 'title', 'description', 'image_url', 'category', 'condition', 'created_at']


class ExchangeProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeProposal
        fields = [
            'id',
            'ad_sender',
            'ad_receiver',
            'comment',
            'status',
            'created_at',
        ]
        read_only_fields = ['status', 'created_at']

    def validate_ad_sender(self, ad_sender):
        user = self.context['request'].user
        if ad_sender.user != user:
            raise serializers.ValidationError("Вы можете предлагать только свои объявления.")
        return ad_sender

    def validate(self, data):
        request = self.context['request']
        target_ad = self.context['view'].get_target_ad()
        if ad_sender := data.get('ad_sender'):
            if ad_sender.pk == target_ad.pk:
                raise serializers.ValidationError("Нельзя обмениваться одним и тем же объявлением.")
        data['ad_receiver'] = target_ad
        return data

    def create(self, validated_data):
        return super().create(validated_data)