from django.db import models


class ExhibitionStatus(models.TextChoices):
    DRAFT = 'draft', '草稿'
    PUBLISHED = 'published', '已发布'
    ONGOING = 'ongoing', '进行中'
    ENDED = 'ended', '已结束'
    CANCELLED = 'cancelled', '已取消'


class Exhibition(models.Model):
    name = models.CharField(max_length=200, verbose_name='展会名称')
    subtitle = models.CharField(max_length=300, blank=True, null=True, verbose_name='副标题')
    description = models.TextField(blank=True, null=True, verbose_name='展会介绍')
    cover_image = models.ImageField(upload_to='exhibitions/', blank=True, null=True, verbose_name='封面图')
    venue = models.CharField(max_length=200, verbose_name='举办地点')
    address = models.CharField(max_length=500, blank=True, null=True, verbose_name='详细地址')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    open_time = models.TimeField(default='09:00', verbose_name='开放时间')
    close_time = models.TimeField(default='17:00', verbose_name='闭馆时间')
    status = models.CharField(
        max_length=20,
        choices=ExhibitionStatus.choices,
        default=ExhibitionStatus.DRAFT,
        verbose_name='状态',
    )
    organizer_contact = models.CharField(max_length=200, blank=True, null=True, verbose_name='主办方联系方式')
    max_visitors = models.IntegerField(default=5000, verbose_name='最大观众人数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'cf_exhibitions'
        ordering = ['-start_date']
        verbose_name = '展会'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.name} ({self.start_date}~{self.end_date})'

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    @property
    def is_active(self):
        return self.status in [ExhibitionStatus.PUBLISHED, ExhibitionStatus.ONGOING]
