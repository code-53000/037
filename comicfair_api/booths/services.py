from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from django.db import transaction
from django.db.models import Q

from .models import Booth, BoothZone, BoothStatus
from applications.models import BoothApplication, ApplicationStatus


@dataclass
class BoothGridPosition:
    grid_x: int
    grid_y: int
    width_units: int = 1
    height_units: int = 1

    def covers(self, x: int, y: int) -> bool:
        return (
            self.grid_x <= x < self.grid_x + self.width_units
            and self.grid_y <= y < self.grid_y + self.height_units
        )

    def overlaps(self, other: 'BoothGridPosition') -> bool:
        return not (
            self.grid_x + self.width_units <= other.grid_x
            or other.grid_x + other.width_units <= self.grid_x
            or self.grid_y + self.height_units <= other.grid_y
            or other.grid_y + other.height_units <= self.grid_y
        )


@dataclass
class AllocationResult:
    success: bool
    message: str
    booth: Optional[Booth] = None
    conflicts: List[Dict[str, Any]] = field(default_factory=list)


class BoothAllocationService:
    """
    展位分配与冲突检测独立服务。

    职责划分：
    - 负责展位可用性判定（空间冲突 + 状态冲突）
    - 负责展位状态流转（预留 -> 已分配 -> 释放）
    - 不处理业务审核、缴费等其他逻辑

    扩展预留：
    - 多日展期：已在 check_availability 中预留 date 参数
    - 批量展位分配：allocate_booths 方法支持批量
    """

    @staticmethod
    def check_availability(
        booth: Booth,
        ignore_application_id: Optional[int] = None,
        date: Optional[str] = None,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        检查展位是否可用。

        Args:
            booth: 目标展位
            ignore_application_id: 忽略该申请ID（用于修改申请时的冲突检查）
            date: 展期日期（预留多日展期扩展）

        Returns:
            (是否可用, 冲突详情列表)
        """
        conflicts = []

        if booth.status == BoothStatus.MAINTENANCE:
            conflicts.append({
                'type': 'status',
                'reason': '展位处于维护中',
            })
            return False, conflicts

        if booth.status == BoothStatus.RESERVED:
            conflicts.append({
                'type': 'status',
                'reason': '展位已被预留',
            })

        occupied_apps = BoothApplication.objects.filter(
            booth=booth,
            status__in=[
                ApplicationStatus.APPROVED,
                ApplicationStatus.PAID,
                ApplicationStatus.CHECKED_IN,
            ],
        )
        if ignore_application_id:
            occupied_apps = occupied_apps.exclude(id=ignore_application_id)

        for app in occupied_apps:
            conflicts.append({
                'type': 'application',
                'application_id': app.id,
                'applicant': app.applicant.username,
                'club_name': app.club_name,
                'status': app.get_status_display(),
            })

        return len(conflicts) == 0, conflicts

    @staticmethod
    def check_grid_conflict(
        zone: BoothZone,
        position: BoothGridPosition,
        exclude_booth_id: Optional[int] = None,
    ) -> Tuple[bool, List[Booth]]:
        """
        检查展区内网格坐标冲突。

        Returns:
            (是否无冲突, 冲突展位列表)
        """
        booths = Booth.objects.filter(zone=zone)
        if exclude_booth_id:
            booths = booths.exclude(id=exclude_booth_id)

        conflicts = []
        for existing in booths:
            existing_pos = BoothGridPosition(
                grid_x=existing.grid_x,
                grid_y=existing.grid_y,
                width_units=existing.width_units,
                height_units=existing.height_units,
            )
            if position.overlaps(existing_pos):
                conflicts.append(existing)

        return len(conflicts) == 0, conflicts

    @classmethod
    def allocate_booth(
        cls,
        booth: Booth,
        application: BoothApplication,
    ) -> AllocationResult:
        """
        为通过审核的摊位申请分配展位。

        原子操作：通过数据库事务保证一致性。
        """
        with transaction.atomic():
            booth_locked = Booth.objects.select_for_update().get(pk=booth.pk)
            available, conflicts = cls.check_availability(
                booth_locked,
                ignore_application_id=application.id,
            )

            if not available:
                return AllocationResult(
                    success=False,
                    message='展位不可用',
                    conflicts=conflicts,
                )

            booth_locked.status = BoothStatus.OCCUPIED
            booth_locked.save()

            application.booth = booth_locked
            application.status = ApplicationStatus.APPROVED
            application.save()

            return AllocationResult(
                success=True,
                message='展位分配成功',
                booth=booth_locked,
            )

    @classmethod
    def allocate_booths(
        cls,
        booths: List[Booth],
        application: BoothApplication,
    ) -> AllocationResult:
        """
        批量分配展位（支持大摊位多格申请）。
        """
        if not booths:
            return AllocationResult(success=False, message='展位列表为空')

        with transaction.atomic():
            all_conflicts = []
            locked_booths = []
            for booth in booths:
                booth_locked = Booth.objects.select_for_update().get(pk=booth.pk)
                available, conflicts = cls.check_availability(
                    booth_locked,
                    ignore_application_id=application.id,
                )
                all_conflicts.extend(conflicts)
                locked_booths.append(booth_locked)

            if all_conflicts:
                return AllocationResult(
                    success=False,
                    message='部分展位不可用',
                    conflicts=all_conflicts,
                )

            for booth_locked in locked_booths:
                booth_locked.status = BoothStatus.OCCUPIED
                booth_locked.save()

            application.booths.set(locked_booths)
            if len(locked_booths) > 0:
                application.booth = locked_booths[0]
            application.status = ApplicationStatus.APPROVED
            application.save()

            return AllocationResult(
                success=True,
                message=f'成功分配 {len(locked_booths)} 个展位',
                booth=locked_booths[0] if locked_booths else None,
            )

    @classmethod
    def release_booth(cls, booth: Booth) -> AllocationResult:
        """
        释放展位（申请取消/拒绝/结束后调用）。
        """
        with transaction.atomic():
            booth_locked = Booth.objects.select_for_update().get(pk=booth.pk)
            booth_locked.status = BoothStatus.AVAILABLE
            booth_locked.save()

            BoothApplication.objects.filter(
                booth=booth_locked,
            ).exclude(
                status__in=[ApplicationStatus.REJECTED, ApplicationStatus.CANCELLED],
            ).update(booth=None)

            return AllocationResult(
                success=True,
                message='展位已释放',
                booth=booth_locked,
            )

    @classmethod
    def reserve_booth(cls, booth: Booth) -> AllocationResult:
        """
        预留展位（主办方临时保留）。
        """
        with transaction.atomic():
            booth_locked = Booth.objects.select_for_update().get(pk=booth.pk)
            if booth_locked.status != BoothStatus.AVAILABLE:
                return AllocationResult(
                    success=False,
                    message=f'展位当前状态为 {booth_locked.get_status_display()}，无法预留',
                )
            booth_locked.status = BoothStatus.RESERVED
            booth_locked.save()
            return AllocationResult(
                success=True,
                message='展位已预留',
                booth=booth_locked,
            )

    @staticmethod
    def get_available_booths(zone: BoothZone) -> List[Booth]:
        """
        获取展区内所有可用展位。
        """
        occupied_booth_ids = BoothApplication.objects.filter(
            booth__zone=zone,
            status__in=[
                ApplicationStatus.APPROVED,
                ApplicationStatus.PAID,
                ApplicationStatus.CHECKED_IN,
            ],
        ).values_list('booth_id', flat=True)

        return list(
            Booth.objects.filter(
                zone=zone,
                status=BoothStatus.AVAILABLE,
            ).exclude(id__in=occupied_booth_ids)
        )

    @staticmethod
    def get_zone_booth_map(zone: BoothZone) -> Dict[str, Any]:
        """
        获取展区的完整展位状态图（用于前端渲染展位图）。
        """
        booths = Booth.objects.filter(zone=zone).select_related('zone')

        occupied_booth_map = {}
        occupied_apps = BoothApplication.objects.filter(
            booth__zone=zone,
            status__in=[
                ApplicationStatus.PENDING,
                ApplicationStatus.APPROVED,
                ApplicationStatus.PAID,
                ApplicationStatus.CHECKED_IN,
            ],
        ).select_related('applicant')

        for app in occupied_apps:
            if app.booth_id:
                occupied_booth_map[app.booth_id] = {
                    'application_id': app.id,
                    'club_name': app.club_name,
                    'applicant': app.applicant.username,
                    'status': app.status,
                    'status_display': app.get_status_display(),
                }

        result = {
            'zone_id': zone.id,
            'zone_name': zone.name,
            'zone_type': zone.zone_type,
            'color': zone.color,
            'position_x': zone.position_x,
            'position_y': zone.position_y,
            'width': zone.width,
            'height': zone.height,
            'booth_price': str(zone.booth_price),
            'booths': [],
            'stats': {
                'total': 0,
                'available': 0,
                'occupied': 0,
                'reserved': 0,
                'maintenance': 0,
            },
        }

        for booth in booths:
            booth_info = {
                'id': booth.id,
                'booth_code': booth.booth_code,
                'status': booth.status,
                'status_display': booth.get_status_display(),
                'grid_x': booth.grid_x,
                'grid_y': booth.grid_y,
                'width_units': booth.width_units,
                'height_units': booth.height_units,
                'has_electricity': booth.has_electricity,
                'has_table': booth.has_table,
                'has_chair': booth.has_chair,
                'application': occupied_booth_map.get(booth.id),
            }
            result['booths'].append(booth_info)

            result['stats']['total'] += 1
            if booth.status == BoothStatus.AVAILABLE and booth.id not in occupied_booth_map:
                result['stats']['available'] += 1
            elif booth.status in (BoothStatus.OCCUPIED,):
                result['stats']['occupied'] += 1
            elif booth.status == BoothStatus.RESERVED:
                result['stats']['reserved'] += 1
            elif booth.status == BoothStatus.MAINTENANCE:
                result['stats']['maintenance'] += 1
            if booth.id in occupied_booth_map:
                result['stats']['occupied'] += 1

        return result
