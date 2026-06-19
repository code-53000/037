from django.db import models
from exhibitions.models import Exhibition


class ZoneType(models.TextChoices):
    GENERAL = 'general', '普通展区'
    PREMIUM = 'premium', '精品展区'
    COSPLAY = 'cosplay', 'Cosplay专区'
    FOOD = 'food', '餐饮区'
    ACTIVITY = 'activity', '活动舞台'


class BoothStatus(models.TextChoices):
    AVAILABLE = 'available', '可申请'
    RESERVED = 'reserved', '已预留'
    OCCUPIED = 'occupied', '已分配'
    MAINTENANCE = 'maintenance', '维护中'


class BoothZone(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='zones',
        verbose_name='所属展会',
    )
    name = models.CharField(max_length=100, verbose_name='展区名称')
    zone_type = models.CharField(
        max_length=20,
        choices=ZoneType.choices,
        default=ZoneType.GENERAL,
        verbose_name='展区类型',
    )
    description = models.TextField(blank=True, null=True, verbose_name='展区说明')
    color = models.CharField(max_length=20, default='#409EFF', verbose_name='标识颜色')
    position_x = models.IntegerField(default=0, verbose_name='平面图X坐标')
    position_y = models.IntegerField(default=0, verbose_name='平面图Y坐标')
    width = models.IntegerField(default=100, verbose_name='展区宽度')
    height = models.IntegerField(default=100, verbose_name='展区高度')
    booth_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='单个展位价格',
    )
    booth_width_meters = models.FloatField(default=1.5, verbose_name='展位宽度(米)')
    booth_depth_meters = models.FloatField(default=1.5, verbose_name='展位进深(米)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'cf_booth_zones'
        ordering = ['exhibition', 'position_y', 'position_x']
        verbose_name = '展区'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'[{self.exhibition.name}] {self.name}'


class Booth(models.Model):
    zone = models.ForeignKey(
        BoothZone,
        on_delete=models.CASCADE,
        related_name='booths',
        verbose_name='所属展区',
    )
    booth_code = models.CharField(max_length=50, verbose_name='展位编号')
    status = models.CharField(
        max_length=20,
        choices=BoothStatus.choices,
        default=BoothStatus.AVAILABLE,
        verbose_name='展位状态',
    )
    grid_x = models.IntegerField(default=0, verbose_name='网格X坐标')
    grid_y = models.IntegerField(default=0, verbose_name='网格Y坐标')
    width_units = models.IntegerField(default=1, verbose_name='占用宽度(单位格)')
    height_units = models.IntegerField(default=1, verbose_name='占用高度(单位格)')
    has_electricity = models.BooleanField(default=True, verbose_name='是否有电')
    has_table = models.BooleanField(default=True, verbose_name='是否有桌子')
    has_chair = models.BooleanField(default=True, verbose_name='是否有椅子')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'cf_booths'
        ordering = ['zone', 'grid_y', 'grid_x']
        unique_together = [('zone', 'booth_code')]
        verbose_name = '展位'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.zone.name} - {self.booth_code}'

    @property
    def exhibition(self):
        return self.zone.exhibition

    @property
    def full_code(self):
        return f'{self.zone.name}-{self.booth_code}'

    @property
    def is_available(self):
        return self.status == BoothStatus.AVAILABLE
