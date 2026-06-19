from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from .models import TicketTier, Ticket, TicketType, TicketStatus
from users.models import UserRole


class TicketTierSerializer(serializers.ModelSerializer):
    ticket_type_display = serializers.CharField(
        source='get_ticket_type_display', read_only=True,
    )
    refund_policy_display = serializers.CharField(
        source='get_refund_policy_display', read_only=True,
    )
    remaining = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    exhibition_name = serializers.CharField(
        source='exhibition.name', read_only=True,
    )

    class Meta:
        model = TicketTier
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'sold_count', 'remaining', 'is_available')


class TicketSerializer(serializers.ModelSerializer):
    ticket_type_display = serializers.CharField(
        source='get_ticket_type_display', read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )
    payment_method_display = serializers.SerializerMethodField()
    tier_name = serializers.CharField(source='tier.name', read_only=True)
    exhibition_name = serializers.CharField(source='exhibition.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = (
            'id', 'ticket_no', 'ticket_code', 'status', 'paid_at',
            'payment_transaction_id', 'used_at', 'refunded_at',
            'refund_amount', 'refund_reason', 'created_at',
        )

    def get_payment_method_display(self, obj):
        if obj.payment_method:
            choices = {
                'alipay': '支付宝',
                'wechat': '微信支付',
                'bank': '银行转账',
                'cash': '现场支付',
            }
            return choices.get(obj.payment_method, obj.payment_method)
        return None


class TicketPurchaseSerializer(serializers.Serializer):
    tier_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1, max_value=10)
    holder_name = serializers.CharField(required=False, allow_null=True, max_length=50)
    holder_phone = serializers.CharField(required=False, allow_null=True, max_length=20)
    payment_method = serializers.ChoiceField(
        choices=[('alipay', '支付宝'), ('wechat', '微信支付'), ('cash', '现场支付')],
        required=False,
        default='wechat',
    )

    def validate_tier_id(self, value):
        try:
            tier = TicketTier.objects.select_for_update().get(pk=value)
        except TicketTier.DoesNotExist:
            raise serializers.ValidationError('票档不存在')
        if not tier.is_available:
            raise serializers.ValidationError('该票档当前不可购买')
        return value

    def validate_quantity(self, value):
        tier_id = self.initial_data.get('tier_id')
        if tier_id:
            try:
                tier = TicketTier.objects.get(pk=tier_id)
                if value > tier.max_per_order:
                    raise serializers.ValidationError(
                        f'单次最多购买 {tier.max_per_order} 张',
                    )
                if tier.quantity > 0 and value > tier.remaining:
                    raise serializers.ValidationError(
                        f'剩余票数不足，剩余 {tier.remaining} 张',
                    )
            except TicketTier.DoesNotExist:
                pass
        return value

    @transaction.atomic
    def save(self):
        user = self.context['request'].user
        data = self.validated_data
        tier = TicketTier.objects.select_for_update().get(pk=data['tier_id'])
        quantity = data['quantity']

        tickets = []
        for i in range(quantity):
            ticket = Ticket(
                user=user,
                exhibition=tier.exhibition,
                tier=tier,
                ticket_type=tier.ticket_type,
                status=TicketStatus.PAID,
                holder_name=data.get('holder_name') or user.real_name,
                holder_phone=data.get('holder_phone') or user.phone,
                price=tier.price,
                payment_method=data['payment_method'],
                paid_at=timezone.now(),
                valid_from=tier.exhibition.start_date,
                valid_to=tier.exhibition.end_date,
            )
            if tier.valid_date:
                ticket.valid_from = tier.valid_date
                ticket.valid_to = tier.valid_date
            ticket.save()
            tickets.append(ticket)

        tier.sold_count += quantity
        tier.save()

        return tickets


class TicketVerifySerializer(serializers.Serializer):
    ticket_code = serializers.CharField(required=True, max_length=64)

    def validate(self, attrs):
        code = attrs.get('ticket_code', '').strip().upper()
        try:
            ticket = Ticket.objects.select_related('tier', 'exhibition').get(ticket_code=code)
        except Ticket.DoesNotExist:
            raise serializers.ValidationError('无效的票码')
        if ticket.status == TicketStatus.USED:
            raise serializers.ValidationError(f'该票已使用（{ticket.used_at}）')
        if ticket.status == TicketStatus.REFUNDED:
            raise serializers.ValidationError('该票已退票')
        if ticket.status == TicketStatus.CANCELLED:
            raise serializers.ValidationError('该票已取消')
        if not ticket.is_valid:
            raise serializers.ValidationError('该票当前不在有效期内或未支付')
        attrs['_ticket'] = ticket
        return attrs

    def save(self):
        ticket = self.validated_data['_ticket']
        ticket.status = TicketStatus.USED
        ticket.used_at = timezone.now()
        ticket.save()
        return ticket


class TicketRefundSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_null=True, max_length=500)
    refund_amount = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2,
    )

    def validate(self, attrs):
        ticket = self.instance
        if ticket.status not in [TicketStatus.PAID, TicketStatus.UNPAID]:
            raise serializers.ValidationError('当前状态无法退票')
        now = timezone.now()
        if ticket.tier.refund_policy == 'no_refund':
            raise serializers.ValidationError('该票种不退不换')
        if ticket.tier.refund_deadline and now > ticket.tier.refund_deadline:
            raise serializers.ValidationError('已超过退票截止时间')
        return attrs

    def save(self):
        ticket = self.instance
        data = self.validated_data
        refund_amount = data.get('refund_amount')
        if refund_amount is None:
            if ticket.tier.refund_policy == 'full_refund':
                refund_amount = ticket.price
            else:
                refund_amount = ticket.price * 0.8
        ticket.status = TicketStatus.REFUNDED
        ticket.refunded_at = timezone.now()
        ticket.refund_amount = refund_amount
        ticket.refund_reason = data.get('reason')
        ticket.tier.sold_count = max(0, ticket.tier.sold_count - 1)
        ticket.tier.save()
        ticket.save()
        return ticket
