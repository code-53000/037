import uuid
from django.db import models
from django.conf import settings

from exhibitions.models import Exhibition


def _generate_ticket_no():
    return 'TK' + uuid.uuid4().hex[:14].upper()


def _generate_ticket_code():
    return 'TC' + uuid.uuid4().hex[:14].upper()


class TicketType(models.TextChoices):
    SINGLE_DAY = 'single_day', '单日票'
    MULTI_DAY = 'multi_day', '通票'
    VIP = 'vip', 'VIP票'
    EXHIBITOR = 'exhibitor', '参展商证'
    MEDIA = 'media', '媒体证'
    STAFF = 'staff', '工作人员证'


class TicketStatus(models.TextChoices):
    UNPAID = 'unpaid', '待支付'
    PAID = 'paid', '已支付'
    USED = 'used', '已使用'
    REFUNDED = 'refunded', '已退票'
    CANCELLED = 'cancelled', '已取消'
    EXPIRED = 'expired', '已过期'


class RefundPolicy(models.TextChoices):
    NO_REFUND = 'no_refund', '不退不换'
    FULL_REFUND = 'full_refund', '全额退款'
    PARTIAL_REFUND = 'partial_refund', '部分退款'


class TicketTier(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='ticket_tiers',
        verbose_name='所属展会',
    )
    name = models.CharField(max_length=100, verbose_name='票种名称')
    ticket_type = models.CharField(
        max_length=20,
        choices=TicketType.choices,
        default=TicketType.SINGLE_DAY,
        verbose_name='票类型',
    )
    description = models.TextField(blank=True, null=True, verbose_name='票种说明')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='票价',
    )
    quantity = models.IntegerField(default=0, verbose_name='总票量（0为不限量）')
    sold_count = models.IntegerField(default=0, verbose_name='已售数量')
    max_per_order = models.IntegerField(default=5, verbose_name='单账号限购')
    on_sale = models.BooleanField(default=True, verbose_name='是否在售')
    sale_start_time = models.DateTimeField(null=True, blank=True, verbose_name='开售时间')
    sale_end_time = models.DateTimeField(null=True, blank=True, verbose_name='停售时间')
    valid_date = models.DateField(null=True, blank=True, verbose_name='有效日期（单日票）')
    refund_policy = models.CharField(
        max_length=20,
        choices=RefundPolicy.choices,
        default=RefundPolicy.NO_REFUND,
        verbose_name='退票政策',
    )
    refund_deadline = models.DateTimeField(null=True, blank=True, verbose_name='退票截止时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'cf_ticket_tiers'
        ordering = ['exhibition', 'price']
        verbose_name = '票档配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'[{self.exhibition.name}] {self.name} (¥{self.price})'

    @property
    def remaining(self):
        if self.quantity == 0:
            return -1
        return max(0, self.quantity - self.sold_count)

    @property
    def is_available(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.on_sale:
            return False
        if self.sale_start_time and now < self.sale_start_time:
            return False
        if self.sale_end_time and now > self.sale_end_time:
            return False
        if self.quantity > 0 and self.remaining <= 0:
            return False
        return True


class Ticket(models.Model):
    ticket_no = models.CharField(
        max_length=32,
        unique=True,
        default=_generate_ticket_no,
        verbose_name='票号',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='持票人',
    )
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='所属展会',
    )
    tier = models.ForeignKey(
        TicketTier,
        on_delete=models.PROTECT,
        related_name='tickets',
        verbose_name='票档',
    )
    ticket_type = models.CharField(
        max_length=20,
        choices=TicketType.choices,
        verbose_name='票类型',
    )
    ticket_code = models.CharField(
        max_length=64,
        unique=True,
        default=_generate_ticket_code,
        verbose_name='入场核验码',
    )
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.UNPAID,
        verbose_name='票状态',
    )
    holder_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='持票人姓名')
    holder_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='持票人电话')
    holder_id_card = models.CharField(max_length=30, blank=True, null=True, verbose_name='身份证号')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='实际支付金额')
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('alipay', '支付宝'),
            ('wechat', '微信支付'),
            ('bank', '银行转账'),
            ('cash', '现场支付'),
        ],
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
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用时间')
    refunded_at = models.DateTimeField(null=True, blank=True, verbose_name='退票时间')
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='退款金额',
    )
    refund_reason = models.TextField(blank=True, null=True, verbose_name='退票原因')
    valid_from = models.DateField(null=True, blank=True, verbose_name='有效开始日期')
    valid_to = models.DateField(null=True, blank=True, verbose_name='有效结束日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'cf_tickets'
        ordering = ['-created_at']
        verbose_name = '门票'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.ticket_no} - {self.tier.name} ({self.get_status_display()})'

    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now().date()
        if self.status != TicketStatus.PAID:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True
