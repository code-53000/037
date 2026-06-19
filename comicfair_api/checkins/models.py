from django.db import models
from django.conf import settings

from exhibitions.models import Exhibition


class CheckInType(models.TextChoices):
    TICKET = 'ticket', '观众门票'
    EXHIBITOR = 'exhibitor', '摊主凭证'
    STAFF = 'staff', '工作人员'
    MEDIA = 'media', '媒体'
    VIP = 'vip', 'VIP通道'


class CheckInStatus(models.TextChoices):
    SUCCESS = 'success', '核验通过'
    ALREADY_CHECKED = 'already_checked', '重复签到'
    INVALID_CODE = 'invalid_code', '凭证无效'
    EXPIRED = 'expired', '凭证过期'
    NOT_PAID = 'not_paid', '未支付'


class CheckInGate(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='checkin_gates',
        verbose_name='所属展会',
    )
    name = models.CharField(max_length=100, verbose_name='通道名称')
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name='通道位置')
    gate_type = models.CharField(
        max_length=20,
        choices=CheckInType.choices,
        default=CheckInType.TICKET,
        verbose_name='通道类型',
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'cf_checkin_gates'
        ordering = ['exhibition', 'name']
        verbose_name = '签到通道'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'[{self.exhibition.name}] {self.name}'


class CheckIn(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='checkins',
        verbose_name='所属展会',
    )
    gate = models.ForeignKey(
        CheckInGate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkins',
        verbose_name='签到通道',
    )
    checkin_type = models.CharField(
        max_length=20,
        choices=CheckInType.choices,
        verbose_name='签到类型',
    )
    status = models.CharField(
        max_length=30,
        choices=CheckInStatus.choices,
        default=CheckInStatus.SUCCESS,
        verbose_name='核验状态',
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operated_checkins',
        verbose_name='操作人',
    )
    code_used = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='使用的核验码',
    )
    ticket_id = models.IntegerField(null=True, blank=True, verbose_name='关联门票ID')
    application_id = models.IntegerField(null=True, blank=True, verbose_name='关联摊位申请ID')
    person_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='人员姓名',
    )
    person_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='人员附加信息',
    )
    checkin_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='签到时间',
    )
    notes = models.TextField(blank=True, null=True, verbose_name='备注')

    class Meta:
        db_table = 'cf_checkins'
        ordering = ['-checkin_time']
        verbose_name = '签到记录'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['exhibition', 'checkin_time']),
            models.Index(fields=['code_used']),
        ]

    def __str__(self):
        return f'{self.get_checkin_type_display()} - {self.person_name or "匿名"} ({self.checkin_time})'
