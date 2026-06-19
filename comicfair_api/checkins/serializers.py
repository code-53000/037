from rest_framework import serializers
from django.utils import timezone

from .models import CheckInGate, CheckIn, CheckInType, CheckInStatus
from tickets.models import Ticket, TicketStatus
from applications.models import BoothApplication, ApplicationStatus
from users.models import UserRole


class CheckInGateSerializer(serializers.ModelSerializer):
    checkin_type_display = serializers.CharField(
        source='get_gate_type_display', read_only=True,
    )
    exhibition_name = serializers.CharField(
        source='exhibition.name', read_only=True,
    )

    class Meta:
        model = CheckInGate
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class CheckInSerializer(serializers.ModelSerializer):
    checkin_type_display = serializers.CharField(
        source='get_checkin_type_display', read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )
    gate_name = serializers.CharField(
        source='gate.name', read_only=True, allow_null=True,
    )
    operator_name = serializers.CharField(
        source='operator.username', read_only=True, allow_null=True,
    )
    exhibition_name = serializers.CharField(
        source='exhibition.name', read_only=True,
    )

    class Meta:
        model = CheckIn
        fields = '__all__'
        read_only_fields = ('id', 'checkin_time')


class CheckInVerifySerializer(serializers.Serializer):
    code = serializers.CharField(required=True, max_length=64)
    gate_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_gate_id(self, value):
        if value:
            try:
                CheckInGate.objects.get(pk=value)
            except CheckInGate.DoesNotExist:
                raise serializers.ValidationError('签到通道不存在')
        return value

    def _verify_ticket(self, code: str):
        try:
            ticket = Ticket.objects.select_related(
                'tier', 'exhibition', 'user',
            ).get(ticket_code=code)
        except Ticket.DoesNotExist:
            return None, {
                'type': CheckInType.TICKET,
                'status': CheckInStatus.INVALID_CODE,
                'message': '无效的票码',
            }

        now = timezone.now()

        if ticket.status == TicketStatus.USED:
            return ticket, {
                'type': CheckInType.TICKET,
                'status': CheckInStatus.ALREADY_CHECKED,
                'message': f'该票已使用（{ticket.used_at}）',
                'ticket': ticket,
            }
        if ticket.status == TicketStatus.REFUNDED:
            return ticket, {
                'type': CheckInType.TICKET,
                'status': CheckInStatus.INVALID_CODE,
                'message': '该票已退票',
                'ticket': ticket,
            }
        if ticket.status != TicketStatus.PAID:
            return ticket, {
                'type': CheckInType.TICKET,
                'status': CheckInStatus.NOT_PAID,
                'message': '该票未支付',
                'ticket': ticket,
            }
        today = now.date()
        if ticket.valid_from and today < ticket.valid_from:
            return ticket, {
                'type': CheckInType.TICKET,
                'status': CheckInStatus.EXPIRED,
                'message': f'该票仅在 {ticket.valid_from} 起有效',
                'ticket': ticket,
            }
        if ticket.valid_to and today > ticket.valid_to:
            return ticket, {
                'type': CheckInType.TICKET,
                'status': CheckInStatus.EXPIRED,
                'message': f'该票已于 {ticket.valid_to} 过期',
                'ticket': ticket,
            }

        ticket.status = TicketStatus.USED
        ticket.used_at = now
        ticket.save()

        return ticket, {
            'type': CheckInType.TICKET,
            'status': CheckInStatus.SUCCESS,
            'message': f'欢迎！{ticket.tier.name}',
            'ticket': ticket,
            'person_name': ticket.holder_name or ticket.user.real_name or ticket.user.username,
            'person_info': {
                'ticket_type': ticket.get_ticket_type_display(),
                'tier_name': ticket.tier.name,
                'price': str(ticket.price),
                'ticket_no': ticket.ticket_no,
            },
        }

    def _verify_exhibitor(self, code: str):
        try:
            application = BoothApplication.objects.select_related(
                'applicant', 'exhibition', 'booth', 'booth__zone',
            ).get(check_in_code=code)
        except BoothApplication.DoesNotExist:
            return None, {
                'type': CheckInType.EXHIBITOR,
                'status': CheckInStatus.INVALID_CODE,
                'message': '无效的摊主核验码',
            }

        now = timezone.now()

        if application.status == ApplicationStatus.CHECKED_IN:
            return application, {
                'type': CheckInType.EXHIBITOR,
                'status': CheckInStatus.ALREADY_CHECKED,
                'message': f'该摊位已签到（{application.checked_in_at}）',
                'application': application,
            }
        if application.status not in [ApplicationStatus.PAID, ApplicationStatus.APPROVED]:
            return application, {
                'type': CheckInType.EXHIBITOR,
                'status': CheckInStatus.NOT_PAID,
                'message': f'当前状态：{application.get_status_display()}',
                'application': application,
            }

        application.status = ApplicationStatus.CHECKED_IN
        application.checked_in_at = now
        application.checked_in_by = self.context['request'].user
        application.save()

        return application, {
            'type': CheckInType.EXHIBITOR,
            'status': CheckInStatus.SUCCESS,
            'message': f'欢迎！{application.club_name}',
            'application': application,
            'person_name': application.contact_name,
            'person_info': {
                'club_name': application.club_name,
                'booth': application.booth.full_code if application.booth else None,
                'zone': application.preferred_zone.name if application.preferred_zone else None,
                'phone': application.contact_phone,
            },
        }

    def validate(self, attrs):
        code = attrs.get('code', '').strip().upper()
        gate_id = attrs.get('gate_id')

        if code.startswith('BT'):
            obj, result = self._verify_exhibitor(code)
        elif code.startswith('TC') or len(code) >= 10:
            obj, result = self._verify_ticket(code)
        else:
            obj, result = self._verify_ticket(code)
            if result['status'] == CheckInStatus.INVALID_CODE:
                obj, result = self._verify_exhibitor(code)

        attrs['_result'] = result
        attrs['_obj'] = obj
        attrs['_gate_id'] = gate_id
        attrs['_code'] = code
        return attrs

    def save(self):
        result = self.validated_data['_result']
        obj = self.validated_data['_obj']
        gate_id = self.validated_data['_gate_id']
        code = self.validated_data['_code']
        user = self.context['request'].user

        exhibition = None
        if obj:
            if hasattr(obj, 'exhibition'):
                exhibition = obj.exhibition

        gate = None
        if gate_id:
            try:
                gate = CheckInGate.objects.get(pk=gate_id)
                if not exhibition:
                    exhibition = gate.exhibition
            except CheckInGate.DoesNotExist:
                pass

        checkin = CheckIn.objects.create(
            exhibition=exhibition,
            gate=gate,
            checkin_type=result['type'],
            status=result['status'],
            operator=user,
            code_used=code,
            ticket_id=obj.id if isinstance(obj, Ticket) else None,
            application_id=obj.id if isinstance(obj, BoothApplication) else None,
            person_name=result.get('person_name'),
            person_info=result.get('person_info', {}),
        )

        return {
            'checkin': CheckInSerializer(checkin).data,
            'result': {
                'status': result['status'],
                'status_display': checkin.get_status_display(),
                'message': result['message'],
                'type': result['type'],
                'type_display': checkin.get_checkin_type_display(),
                'person_name': result.get('person_name'),
                'person_info': result.get('person_info', {}),
            },
        }
