from django.db import models
from django.conf import settings

from exhibitions.models import Exhibition
from booths.models import Booth, BoothZone


class ApplicationStatus(models.TextChoices):
    DRAFT = 'draft', '草稿'
    PENDING = 'pending', '待审核'
    APPROVED = 'approved', '审核通过(待缴费)'
    REJECTED = 'rejected', '审核驳回'
    PAID = 'paid', '已缴费'
    CANCELLED = 'cancelled', '已取消'
    CHECKED_IN = 'checked_in', '已签到入场'
    COMPLETED = 'completed', '已完成'


class PaymentMethod(models.TextChoices):
    ALIPAY = 'alipay', '支付宝'
    WECHAT = 'wechat', '微信支付'
    BANK = 'bank', '银行转账'
    CASH = 'cash', '现场支付'


class BoothApplication(models.Model):
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='booth_applications',
        verbose_name='申请人',
    )
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='所属展会',
    )
    preferred_zone = models.ForeignKey(
        BoothZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_applications',
        verbose_name='意向展区',
    )
    booth = models.ForeignKey(
        Booth,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        verbose_name='分配展位',
    )
    booths = models.ManyToManyField(
        Booth,
        blank=True,
        related_name='multi_applications',
        verbose_name='分配展位(多)',
    )
    booth_count = models.IntegerField(default=1, verbose_name='申请展位数量')
    club_name = models.CharField(max_length=200, verbose_name='社团/摊位名称')
    club_introduction = models.TextField(blank=True, null=True, verbose_name='社团简介')
    works_type = models.CharField(max_length=200, blank=True, null=True, verbose_name='参展作品类型')
    main_works = models.TextField(blank=True, null=True, verbose_name='主要作品介绍')
    contact_name = models.CharField(max_length=50, verbose_name='联系人姓名')
    contact_phone = models.CharField(max_length=20, verbose_name='联系电话')
    contact_email = models.EmailField(max_length=100, blank=True, null=True, verbose_name='联系邮箱')
    social_media = models.CharField(max_length=500, blank=True, null=True, verbose_name='社交媒体账号')
    has_power = models.BooleanField(default=False, verbose_name='是否需要额外用电')
    power_description = models.CharField(max_length=200, blank=True, null=True, verbose_name='用电需求说明')
    special_requirements = models.TextField(blank=True, null=True, verbose_name='特殊需求')
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        verbose_name='申请状态',
    )
    review_notes = models.TextField(blank=True, null=True, verbose_name='审核备注')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
        verbose_name='审核人',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='应缴费用',
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='实缴费用',
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        null=True,
        verbose_name='支付方式',
    )
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')
    payment_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='支付交易号',
    )
    check_in_code = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        verbose_name='签到核验码',
    )
    checked_in_at = models.DateTimeField(null=True, blank=True, verbose_name='签到时间')
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_in_applications',
        verbose_name='签到核验人',
    )
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'cf_booth_applications'
        ordering = ['-created_at']
        verbose_name = '摊位申请'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.club_name} - {self.exhibition.name} ({self.get_status_display()})'

    @property
    def is_pending_review(self):
        return self.status == ApplicationStatus.PENDING

    @property
    def is_approved(self):
        return self.status in [ApplicationStatus.APPROVED, ApplicationStatus.PAID, ApplicationStatus.CHECKED_IN]

    @property
    def needs_payment(self):
        return self.status == ApplicationStatus.APPROVED and self.fee_amount > self.paid_amount
