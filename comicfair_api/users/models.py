from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    ORGANIZER = 'organizer', '主办方'
    EXHIBITOR = 'exhibitor', '参展摊主'
    VISITOR = 'visitor', '观众'


class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('用户名必须填写')
        email = self.normalize_email(email) if email else None
        extra_fields.setdefault('role', UserRole.VISITOR)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', UserRole.ORGANIZER)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.VISITOR,
        verbose_name='用户角色',
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    real_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='真实姓名')
    organization = models.CharField(max_length=100, blank=True, null=True, verbose_name='社团/组织名称')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')

    objects = UserManager()

    class Meta:
        db_table = 'cf_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
