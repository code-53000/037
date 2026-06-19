import uuid
from rest_framework import serializers
from django.db import transaction

from .models import BoothApplication, ApplicationStatus, PaymentMethod
from booths.models import BoothZone, Booth
from booths.services import BoothAllocationService


class BoothApplicationSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True,
    )
    applicant_name = serializers.CharField(source='applicant.username', read_only=True)
    exhibition_name = serializers.CharField(source='exhibition.name', read_only=True)
    preferred_zone_name = serializers.CharField(
        source='preferred_zone.name', read_only=True, allow_null=True,
    )
    booth_code = serializers.CharField(
        source='booth.full_code', read_only=True, allow_null=True,
    )
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.username', read_only=True, allow_null=True,
    )
    is_pending_review = serializers.BooleanField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    needs_payment = serializers.BooleanField(read_only=True)

    class Meta:
        model = BoothApplication
        fields = '__all__'
        read_only_fields = (
            'id', 'applicant', 'status', 'review_notes', 'reviewed_by',
            'reviewed_at', 'fee_amount', 'paid_amount', 'payment_method',
            'paid_at', 'payment_transaction_id', 'check_in_code',
            'checked_in_at', 'checked_in_by', 'submitted_at',
            'created_at', 'updated_at',
        )

    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)


class BoothApplicationSubmitSerializer(serializers.Serializer):
    def validate(self, attrs):
        instance = self.instance
        if instance.status != ApplicationStatus.DRAFT:
            raise serializers.ValidationError('只有草稿状态的申请可以提交')
        required_fields = [
            'club_name', 'contact_name', 'contact_phone',
            'exhibition', 'preferred_zone',
        ]
        for field in required_fields:
            if not getattr(instance, field, None):
                raise serializers.ValidationError({
                    field: '提交前请填写此字段',
                })
        return attrs


class ApplicationReviewSerializer(serializers.Serializer):
    APPROVE = 'approve'
    REJECT = 'reject'
    action = serializers.ChoiceField(choices=[(APPROVE, '通过'), (REJECT, '驳回')])
    booth_id = serializers.IntegerField(required=False, allow_null=True)
    review_notes = serializers.CharField(required=False, allow_null=True, max_length=1000)
    fee_amount = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2, default=0,
    )

    def validate_booth_id(self, value):
        if value:
            try:
                Booth.objects.get(pk=value)
            except Booth.DoesNotExist:
                raise serializers.ValidationError('指定的展位不存在')
        return value

    @transaction.atomic
    def save(self):
        instance = self.instance
        data = self.validated_data
        action = data['action']
        user = self.context['request'].user

        from django.utils import timezone

        if action == self.REJECT:
            instance.status = ApplicationStatus.REJECTED
            instance.review_notes = data.get('review_notes')
            instance.reviewed_by = user
            instance.reviewed_at = timezone.now()
            instance.save()
            return instance

        booth_id = data.get('booth_id')
        if not booth_id:
            raise serializers.ValidationError({'booth_id': '通过审核时必须指定分配的展位'})

        booth = Booth.objects.get(pk=booth_id)
        result = BoothAllocationService.allocate_booth(booth, instance)
        if not result.success:
            raise serializers.ValidationError({
                'booth_id': f'展位分配失败：{result.message}',
            })

        instance.review_notes = data.get('review_notes')
        instance.fee_amount = data.get('fee_amount', instance.preferred_zone.booth_price if instance.preferred_zone else 0)
        instance.reviewed_by = user
        instance.reviewed_at = timezone.now()
        instance.check_in_code = 'BT' + uuid.uuid4().hex[:14].upper()
        instance.save()
        return instance


class ApplicationPaySerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_transaction_id = serializers.CharField(required=False, allow_null=True, max_length=100)

    def validate(self, attrs):
        instance = self.instance
        if instance.status != ApplicationStatus.APPROVED:
            raise serializers.ValidationError('只有审核通过的申请可以缴费')
        return attrs

    def save(self):
        from django.utils import timezone

        instance = self.instance
        data = self.validated_data
        instance.payment_method = data['payment_method']
        instance.paid_amount = data['paid_amount']
        instance.payment_transaction_id = data.get('payment_transaction_id')
        instance.paid_at = timezone.now()
        if instance.paid_amount >= instance.fee_amount:
            instance.status = ApplicationStatus.PAID
        instance.save()
        return instance


class ApplicationCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_null=True, max_length=500)

    def validate(self, attrs):
        instance = self.instance
        if instance.status in [ApplicationStatus.CHECKED_IN, ApplicationStatus.COMPLETED, ApplicationStatus.CANCELLED]:
            raise serializers.ValidationError('当前状态无法取消申请')
        return attrs

    @transaction.atomic
    def save(self):
        instance = self.instance
        data = self.validated_data

        if instance.booth:
            BoothAllocationService.release_booth(instance.booth)

        if data.get('reason'):
            instance.review_notes = (instance.review_notes or '') + f'\n[取消原因] {data["reason"]}'

        instance.status = ApplicationStatus.CANCELLED
        instance.save()
        return instance


class ApplicationCheckInSerializer(serializers.Serializer):
    check_in_code = serializers.CharField(required=True, max_length=64)

    def validate(self, attrs):
        code = attrs.get('check_in_code', '').strip().upper()
        try:
            application = BoothApplication.objects.get(check_in_code=code)
        except BoothApplication.DoesNotExist:
            raise serializers.ValidationError('无效的签到核验码')
        if application.status not in [ApplicationStatus.PAID, ApplicationStatus.APPROVED]:
            raise serializers.ValidationError(f'当前状态（{application.get_status_display()}）无法签到')
        attrs['_application'] = application
        return attrs

    def save(self):
        from django.utils import timezone

        application = self.validated_data['_application']
        application.status = ApplicationStatus.CHECKED_IN
        application.checked_in_at = timezone.now()
        application.checked_in_by = self.context['request'].user
        application.save()
        return application
