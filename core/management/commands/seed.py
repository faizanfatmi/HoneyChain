import datetime
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.blockchain import add_block
from core.models import Batch, Beekeeper, Block, Hive

BEEKEEPERS = [
    ("Rajesh Kumar Apiaries", "APRY-UP-1042", "Saharanpur, Uttar Pradesh", "Uttar Pradesh", True),
    ("Himalayan Bee Farms", "APRY-UK-2087", "Nainital, Uttarakhand", "Uttarakhand", True),
    ("Sundarbans Honey Collective", "APRY-WB-3311", "South 24 Parganas, West Bengal", "West Bengal", False),
    ("Nilgiri Wild Apiary", "APRY-TN-5590", "The Nilgiris, Tamil Nadu", "Tamil Nadu", True),
]

HIVES = [
    ("HIVE-UP-001", 0, "Mustard", 29.9680, 77.5460),
    ("HIVE-UP-002", 0, "Multiflora", 29.9700, 77.5500),
    ("HIVE-UK-001", 1, "Litchi", 29.3919, 79.4542),
    ("HIVE-WB-001", 2, "Mangrove (Sundarban)", 21.9497, 88.4200),
    ("HIVE-TN-001", 3, "Eucalyptus", 11.4064, 76.6932),
]

HONEY_TYPES = ["Raw Mustard Honey", "Multiflora Forest Honey", "Litchi Blossom Honey",
               "Wild Sundarban Honey", "Eucalyptus Honey"]


class Command(BaseCommand):
    help = "Populate the database with demo beekeepers, hives, batches and chains."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing core data first.")

    def handle(self, *args, **options):
        if options["reset"]:
            Block.objects.all().delete()
            Batch.objects.all().delete()
            Hive.objects.all().delete()
            Beekeeper.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing HoneyChain data cleared."))

        if Batch.objects.exists():
            self.stdout.write("Data already present. Use --reset to rebuild.")
            return

        keepers = []
        for name, reg, loc, state, organic in BEEKEEPERS:
            keepers.append(Beekeeper.objects.create(
                name=name, apiary_reg_no=reg, location=loc, state=state, certified_organic=organic
            ))

        hives = []
        for code, keeper_idx, floral, lat, lng in HIVES:
            hives.append(Hive.objects.create(
                beekeeper=keepers[keeper_idx], code=code, floral_source=floral,
                latitude=lat, longitude=lng,
            ))

        year = timezone.now().year
        for i, hive in enumerate(hives):
            batch = Batch.objects.create(
                code=f"HNY-{year}-{i + 1:04d}",
                hive=hive,
                honey_type=HONEY_TYPES[i],
                harvest_date=timezone.now().date() - datetime.timedelta(days=40 - i * 5),
                quantity_kg=round(random.uniform(18, 60), 2),
            )
            self._build_chain(batch)
            self.stdout.write(self.style.SUCCESS(f"  chained {batch.code} ({batch.block_count} blocks)"))

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {Beekeeper.objects.count()} beekeepers, "
            f"{Hive.objects.count()} hives, {Batch.objects.count()} batches, "
            f"{Block.objects.count()} blocks."
        ))

    def _build_chain(self, batch):
        keeper = batch.hive.beekeeper
        base = timezone.make_aware(
            datetime.datetime.combine(batch.harvest_date, datetime.time(9, 0))
        )

        def when(days, hours=0):
            return base + datetime.timedelta(days=days, hours=hours)

        add_block(batch, event_type=Block.Event.GENESIS, actor="HoneyChain",
                  note="Traceability chain created for this batch.", timestamp=when(0))
        add_block(batch, event_type=Block.Event.HARVEST, actor=keeper.name,
                  location=keeper.location, timestamp=when(0, 2),
                  note=f"{batch.quantity_kg} kg harvested from hive {batch.hive.code}.",
                  data={"floral_source": batch.hive.floral_source})
        add_block(batch, event_type=Block.Event.EXTRACTION, actor=f"{keeper.name} extraction unit",
                  location=keeper.location, timestamp=when(1),
                  note="Cold extraction, no heating above 35°C.", data={"temperature_c": 34.0})
        add_block(batch, event_type=Block.Event.LAB_TEST, actor="AgMark Certified Lab",
                  location=keeper.state, timestamp=when(3),
                  note="Passed FSSAI purity and moisture checks.",
                  data={"moisture_pct": round(random.uniform(16.5, 19.5), 1),
                        "pollen_count": random.randint(45, 95), "c4_sugar": "not detected"})
        add_block(batch, event_type=Block.Event.PROCESSING, actor="Nashik Processing Unit",
                  location="Nashik, Maharashtra", timestamp=when(6),
                  note="Filtered and gently pasteurised.")
        add_block(batch, event_type=Block.Event.PACKAGING, actor="Nashik Processing Unit",
                  location="Nashik, Maharashtra", timestamp=when(7),
                  note="Bottled in 500g glass jars; QR labels applied.", data={"jars": int(float(batch.quantity_kg) * 2)})
        add_block(batch, event_type=Block.Event.WAREHOUSE, actor="Central Warehouse",
                  location="Pune, Maharashtra", timestamp=when(9),
                  note="Stored at controlled temperature.")
        if batch.pk % 2 == 0:
            add_block(batch, event_type=Block.Event.TRANSIT, actor="BlueDart Logistics",
                      location="In transit", timestamp=when(11),
                      note="Dispatched to retail partner.")
            add_block(batch, event_type=Block.Event.RETAIL, actor="Organic Mart",
                      location="Bengaluru, Karnataka", timestamp=when(13),
                      note="Received and placed on shelf.")
            batch.status = Batch.Status.ON_SHELF
        else:
            batch.status = Batch.Status.PACKAGED
        batch.save(update_fields=["status"])
