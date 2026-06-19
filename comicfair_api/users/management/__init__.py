from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from users.models import User, UserRole
from exhibitions.models import Exhibition, ExhibitionStatus
from booths.models import BoothZone, Booth, ZoneType, BoothStatus
from tickets.models import TicketTier, TicketType, RefundPolicy
from applications.models import BoothApplication, ApplicationStatus, PaymentMethod
from checkins.models import CheckInGate, CheckInType
from booths.services import BoothAllocationService
from django.utils import timezone


class Command(BaseCommand):
    help = '初始化漫展平台示例数据（展位图+摊位申请+票务）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新初始化（会清空现有示例数据）',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options.get('force', False)

        if User.objects.filter(username='organizer').exists() and not force:
            self.stdout.write(self.style.SUCCESS('示例数据已存在，跳过初始化。使用 --force 可重新初始化。'))
            return

        if force:
            self.stdout.write(self.style.WARNING('强制模式：将清空所有业务数据...'))
            from django.db import connection
            with connection.cursor() as cursor:
                tables = [
                    'cf_checkins', 'cf_checkin_gates',
                    'cf_tickets', 'cf_ticket_tiers',
                    'cf_booth_applications', 'cf_booths', 'cf_booth_zones',
                    'cf_exhibitions', 'cf_users',
                ]
                for t in tables:
                    try:
                        cursor.execute(f'DELETE FROM {t}')
                    except Exception:
                        pass
            self.stdout.write(self.style.SUCCESS('已清空数据'))

        self._create_users()
        exhibition = self._create_exhibition()
        zones = self._create_zones_and_booths(exhibition)
        self._create_ticket_tiers(exhibition)
        self._create_checkin_gates(exhibition)
        self._create_sample_applications(exhibition, zones)
        self._create_sample_tickets(exhibition)

        self.stdout.write(self.style.SUCCESS('\n========== 初始化完成 =========='))
        self.stdout.write(self.style.SUCCESS('主办方账号: organizer / comicfair2024'))
        self.stdout.write(self.style.SUCCESS('摊主账号: exhibitor1 / comicfair2024'))
        self.stdout.write(self.style.SUCCESS('观众账号: visitor1 / comicfair2024'))
        self.stdout.write(self.style.SUCCESS(f'展会: {exhibition.name}'))
        self.stdout.write(self.style.SUCCESS(f'  展区数: {len(zones)}'))
        self.stdout.write(self.style.SUCCESS(f'  展位总数: {Booth.objects.filter(zone__exhibition=exhibition).count()}'))

    def _create_users(self):
        self.stdout.write('创建用户账号...')

        User.objects.create_superuser(
            username='admin',
            email='admin@comicfair.local',
            password='admin2024',
            role=UserRole.ORGANIZER,
            real_name='系统管理员',
        )

        organizer, _ = User.objects.get_or_create(
            username='organizer',
            defaults=dict(
                email='organizer@comicfair.local',
                role=UserRole.ORGANIZER,
                real_name='漫展主办方',
                organization='同人漫展组委会',
                phone='13800000001',
                is_staff=True,
            ),
        )
        organizer.set_password('comicfair2024')
        organizer.save()

        for i in range(1, 6):
            user, _ = User.objects.get_or_create(
                username=f'exhibitor{i}',
                defaults=dict(
                    email=f'exhibitor{i}@comicfair.local',
                    role=UserRole.EXHIBITOR,
                    real_name=f'摊主{i:02d}',
                    organization=f'社团{i:02d}',
                    phone=f'1380001{i:03d}',
                ),
            )
            user.set_password('comicfair2024')
            user.save()

        for i in range(1, 6):
            user, _ = User.objects.get_or_create(
                username=f'visitor{i}',
                defaults=dict(
                    email=f'visitor{i}@comicfair.local',
                    role=UserRole.VISITOR,
                    real_name=f'观众{i:02d}',
                    phone=f'1390001{i:03d}',
                ),
            )
            user.set_password('comicfair2024')
            user.save()

        self.stdout.write(self.style.SUCCESS('  用户创建完成'))

    def _create_exhibition(self):
        self.stdout.write('创建展会...')
        today = timezone.now().date()
        exhibition, _ = Exhibition.objects.get_or_create(
            name='2026 夏日同人祭',
            defaults=dict(
                subtitle='Summer Comic Fair 2026',
                description='年度最盛大的同人漫展，汇聚百位优秀画师与社团，带来精彩的同人创作展示、Cosplay 表演与主题活动！',
                venue='国家会展中心（上海）',
                address='上海市青浦区崧泽大道 333 号',
                start_date=today,
                end_date=today + timezone.timedelta(days=1),
                open_time='09:00',
                close_time='17:00',
                status=ExhibitionStatus.ONGOING,
                organizer_contact='QQ: 123456789 / 电话: 400-000-1234',
                max_visitors=5000,
            ),
        )
        self.stdout.write(self.style.SUCCESS(f'  展会创建: {exhibition.name}'))
        return exhibition

    def _create_zones_and_booths(self, exhibition):
        self.stdout.write('创建展区与展位...')
        zones_data = [
            {
                'name': 'A区 普通同人',
                'zone_type': ZoneType.GENERAL,
                'description': '普通同人社团展区',
                'color': '#409EFF',
                'pos': (20, 20, 420, 300),
                'price': 800,
                'rows': 6, 'cols': 10, 'prefix': 'A',
            },
            {
                'name': 'B区 精品社团',
                'zone_type': ZoneType.PREMIUM,
                'description': '知名画师&精品社团展区',
                'color': '#E6A23C',
                'pos': (480, 20, 420, 300),
                'price': 1500,
                'rows': 5, 'cols': 8, 'prefix': 'B',
            },
            {
                'name': 'C区 Cosplay',
                'zone_type': ZoneType.COSPLAY,
                'description': 'Cosplay 自由行与摄影区',
                'color': '#F56C6C',
                'pos': (20, 360, 420, 260),
                'price': 600,
                'rows': 4, 'cols': 8, 'prefix': 'C',
            },
            {
                'name': 'D区 餐饮休息',
                'zone_type': ZoneType.FOOD,
                'description': '餐饮与休息区',
                'color': '#67C23A',
                'pos': (480, 360, 420, 260),
                'price': 2000,
                'rows': 3, 'cols': 6, 'prefix': 'D',
            },
        ]

        zones = []
        for zd in zones_data:
            zone, _ = BoothZone.objects.get_or_create(
                exhibition=exhibition,
                name=zd['name'],
                defaults=dict(
                    zone_type=zd['zone_type'],
                    description=zd['description'],
                    color=zd['color'],
                    position_x=zd['pos'][0],
                    position_y=zd['pos'][1],
                    width=zd['pos'][2],
                    height=zd['pos'][3],
                    booth_price=zd['price'],
                ),
            )
            zones.append(zone)

            existing_count = Booth.objects.filter(zone=zone).count()
            if existing_count > 0:
                continue

            booths_to_create = []
            for row in range(zd['rows']):
                for col in range(zd['cols']):
                    code = f'{zd["prefix"]}{row + 1:02d}{col + 1:02d}'
                    booths_to_create.append(Booth(
                        zone=zone,
                        booth_code=code,
                        status=BoothStatus.AVAILABLE,
                        grid_x=col,
                        grid_y=row,
                        width_units=1,
                        height_units=1,
                    ))
            Booth.objects.bulk_create(booths_to_create)
            self.stdout.write(f'  {zd["name"]}: {len(booths_to_create)} 个展位')

        self.stdout.write(self.style.SUCCESS('  展区展位创建完成'))
        return zones

    def _create_ticket_tiers(self, exhibition):
        self.stdout.write('创建票档...')
        tiers_data = [
            {
                'name': '单日票（周六）',
                'ticket_type': TicketType.SINGLE_DAY,
                'price': 68,
                'quantity': 2000,
                'max_per_order': 5,
                'valid_date': exhibition.start_date,
            },
            {
                'name': '单日票（周日）',
                'ticket_type': TicketType.SINGLE_DAY,
                'price': 68,
                'quantity': 2000,
                'max_per_order': 5,
                'valid_date': exhibition.end_date,
            },
            {
                'name': '双日通票',
                'ticket_type': TicketType.MULTI_DAY,
                'price': 118,
                'quantity': 1000,
                'max_per_order': 3,
                'valid_date': None,
            },
            {
                'name': 'VIP 限定票',
                'ticket_type': TicketType.VIP,
                'description': '优先入场 + VIP 纪念礼包 + 限定周边',
                'price': 388,
                'quantity': 200,
                'max_per_order': 2,
                'valid_date': None,
                'refund_policy': RefundPolicy.PARTIAL_REFUND,
            },
        ]

        for td in tiers_data:
            obj, created = TicketTier.objects.get_or_create(
                exhibition=exhibition,
                name=td['name'],
                defaults=td,
            )
            if created:
                self.stdout.write(f'  创建票档: {obj.name} (¥{obj.price})')

        self.stdout.write(self.style.SUCCESS('  票档创建完成'))

    def _create_checkin_gates(self, exhibition):
        self.stdout.write('创建签到通道...')
        gates_data = [
            {'name': '1号门 观众入口', 'location': '展馆东门', 'gate_type': CheckInType.TICKET},
            {'name': '2号门 观众入口', 'location': '展馆西门', 'gate_type': CheckInType.TICKET},
            {'name': '摊主签到台', 'location': '展馆北侧', 'gate_type': CheckInType.EXHIBITOR},
            {'name': 'VIP 快速通道', 'location': '展馆北门', 'gate_type': CheckInType.VIP},
        ]
        for gd in gates_data:
            CheckInGate.objects.get_or_create(
                exhibition=exhibition,
                name=gd['name'],
                defaults=gd,
            )
        self.stdout.write(self.style.SUCCESS('  签到通道创建完成'))

    def _create_sample_applications(self, exhibition, zones):
        self.stdout.write('创建示例摊位申请...')
        import uuid
        now = timezone.now()

        applications_data = [
            {
                'user': 'exhibitor1',
                'club': '星绘社',
                'intro': '专注于东方 Project 同人创作的社团',
                'works_type': '东方Project 同人本/周边',
                'main_works': '东方幻梦谭 第5期',
                'zone_idx': 0,
                'booth_code': 'A0101',
                'status': ApplicationStatus.PAID,
                'fee': 800,
                'paid': 800,
                'power': False,
            },
            {
                'user': 'exhibitor2',
                'club': '砂糖屋',
                'intro': '日系原创插画社团',
                'works_type': '原创插画本/明信片',
                'main_works': '砂糖色的季节',
                'zone_idx': 0,
                'booth_code': 'A0203',
                'status': ApplicationStatus.PAID,
                'fee': 800,
                'paid': 800,
                'power': True,
            },
            {
                'user': 'exhibitor3',
                'club': '白夜画廊',
                'intro': '精品原画与艺术画册',
                'works_type': '原画集/艺术微喷',
                'main_works': '白夜行画集 Vol.3',
                'zone_idx': 1,
                'booth_code': 'B0102',
                'status': ApplicationStatus.APPROVED,
                'fee': 1500,
                'paid': 0,
                'power': True,
            },
            {
                'user': 'exhibitor4',
                'club': '彩虹工坊',
                'intro': '手作玩偶与手工皮具',
                'works_type': '手作/皮具周边',
                'main_works': '原创限定玩偶系列',
                'zone_idx': 0,
                'booth_code': None,
                'status': ApplicationStatus.PENDING,
                'fee': 0,
                'paid': 0,
                'power': False,
            },
            {
                'user': 'exhibitor5',
                'club': '喵食屋',
                'intro': '萌系主题自制零食与饮品',
                'works_type': '餐饮/自制食品',
                'main_works': '猫咪主题曲奇礼盒',
                'zone_idx': 3,
                'booth_code': None,
                'status': ApplicationStatus.DRAFT,
                'fee': 0,
                'paid': 0,
                'power': True,
            },
        ]

        for ad in applications_data:
            user = User.objects.get(username=ad['user'])
            zone = zones[ad['zone_idx']]

            app, created = BoothApplication.objects.get_or_create(
                applicant=user,
                exhibition=exhibition,
                club_name=ad['club'],
                defaults=dict(
                    preferred_zone=zone,
                    booth_count=1,
                    club_introduction=ad['intro'],
                    works_type=ad['works_type'],
                    main_works=ad['main_works'],
                    contact_name=user.real_name,
                    contact_phone=user.phone,
                    contact_email=user.email,
                    has_power=ad['power'],
                    status=ApplicationStatus.DRAFT,
                    submitted_at=now if ad['status'] != ApplicationStatus.DRAFT else None,
                ),
            )

            if not created:
                continue

            booth = None
            if ad['booth_code']:
                booth = Booth.objects.filter(zone=zone, booth_code=ad['booth_code']).first()

            if ad['status'] == ApplicationStatus.DRAFT:
                app.status = ApplicationStatus.DRAFT
                app.save()
                self.stdout.write(f'  [草稿] {ad["club"]} - {zone.name}')
                continue

            app.submitted_at = now
            app.status = ApplicationStatus.PENDING
            app.save()

            if booth and ad['status'] in [ApplicationStatus.APPROVED, ApplicationStatus.PAID, ApplicationStatus.CHECKED_IN]:
                organizer = User.objects.get(username='organizer')
                result = BoothAllocationService.allocate_booth(booth, app)
                if result.success:
                    app.fee_amount = ad['fee']
                    app.reviewed_by = organizer
                    app.reviewed_at = now
                    app.review_notes = '资料审核通过，请及时缴费。'
                    app.check_in_code = 'BT' + uuid.uuid4().hex[:14].upper()
                    app.save()

                    if ad['status'] in [ApplicationStatus.PAID, ApplicationStatus.CHECKED_IN]:
                        app.paid_amount = ad['paid']
                        app.payment_method = PaymentMethod.ALIPAY
                        app.paid_at = now
                        app.payment_transaction_id = f'ALIPAY{uuid.uuid4().hex[:16].upper()}'
                        if ad['paid'] >= ad['fee']:
                            app.status = ApplicationStatus.PAID
                        app.save()

                    if ad['status'] == ApplicationStatus.CHECKED_IN:
                        app.status = ApplicationStatus.CHECKED_IN
                        app.checked_in_at = now
                        app.checked_in_by = organizer
                        app.save()

            self.stdout.write(
                f'  [{app.get_status_display()}] {ad["club"]}'
                f' 展位: {booth.booth_code if booth else "未分配"}'
                f' 费用: {ad["fee"]}/{ad["paid"]}'
            )

        self.stdout.write(self.style.SUCCESS('  示例摊位申请创建完成'))

    def _create_sample_tickets(self, exhibition):
        self.stdout.write('创建示例票务数据...')
        from tickets.models import Ticket, TicketStatus
        import uuid

        tiers = {t.name: t for t in TicketTier.objects.filter(exhibition=exhibition)}

        sample_orders = [
            ('visitor1', '单日票（周六）', 2, 68),
            ('visitor2', '双日通票', 1, 118),
            ('visitor3', 'VIP 限定票', 1, 388),
            ('visitor4', '单日票（周六）', 1, 68),
        ]

        for username, tier_name, qty, unit_price in sample_orders:
            user = User.objects.get(username=username)
            tier = tiers[tier_name]
            for i in range(qty):
                Ticket.objects.get_or_create(
                    user=user,
                    tier=tier,
                    ticket_type=tier.ticket_type,
                    defaults=dict(
                        exhibition=exhibition,
                        status=TicketStatus.PAID,
                        holder_name=user.real_name,
                        holder_phone=user.phone,
                        price=unit_price,
                        payment_method='wechat',
                        paid_at=timezone.now(),
                        valid_from=tier.valid_date or exhibition.start_date,
                        valid_to=tier.valid_date or exhibition.end_date,
                        payment_transaction_id=f'WX{uuid.uuid4().hex[:18].upper()}',
                    ),
                )
            tier.sold_count += qty
            tier.save()

        self.stdout.write(self.style.SUCCESS('  示例票务数据创建完成'))
