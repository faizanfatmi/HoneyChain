from django.db import models
from django.urls import reverse
from django.utils import timezone


class Beekeeper(models.Model):
    name = models.CharField(max_length=120)
    apiary_reg_no = models.CharField("Apiary registration no.", max_length=40, unique=True)
    location = models.CharField(max_length=160)
    state = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    certified_organic = models.BooleanField(default=False)
    joined_on = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.apiary_reg_no})"


class Hive(models.Model):
    beekeeper = models.ForeignKey(Beekeeper, on_delete=models.CASCADE, related_name="hives")
    code = models.CharField(max_length=40, unique=True)
    floral_source = models.CharField(
        max_length=120, help_text="Dominant nectar source, e.g. Mustard, Litchi, Multiflora"
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    installed_on = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} · {self.floral_source}"


class Batch(models.Model):
    class Status(models.TextChoices):
        HARVESTED = "harvested", "Harvested"
        PROCESSING = "processing", "Processing"
        PACKAGED = "packaged", "Packaged"
        IN_TRANSIT = "in_transit", "In transit"
        ON_SHELF = "on_shelf", "On shelf"
        SOLD = "sold", "Sold"

    code = models.CharField(max_length=32, unique=True, db_index=True)
    hive = models.ForeignKey(Hive, on_delete=models.PROTECT, related_name="batches")
    honey_type = models.CharField(max_length=120)
    harvest_date = models.DateField(default=timezone.now)
    quantity_kg = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.HARVESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "batches"

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse("trace", kwargs={"code": self.code})

    @property
    def beekeeper(self):
        return self.hive.beekeeper

    @property
    def block_count(self):
        return self.blocks.count()

    @property
    def latest_block(self):
        return self.blocks.order_by("-index").first()


class Block(models.Model):
    class Event(models.TextChoices):
        GENESIS = "genesis", "Chain created"
        HARVEST = "harvest", "Harvested from hive"
        EXTRACTION = "extraction", "Honey extracted"
        LAB_TEST = "lab_test", "Quality / lab test"
        PROCESSING = "processing", "Processed & filtered"
        PACKAGING = "packaging", "Bottled & labelled"
        WAREHOUSE = "warehouse", "Stored in warehouse"
        TRANSIT = "transit", "Shipped to retailer"
        RETAIL = "retail", "Received by retailer"
        SOLD = "sold", "Sold to consumer"

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="blocks")
    index = models.PositiveIntegerField()
    event_type = models.CharField(max_length=20, choices=Event.choices)
    actor = models.CharField(max_length=160, help_text="Who performed this step")
    location = models.CharField(max_length=160, blank=True)
    note = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True, help_text="Structured metrics for this step")
    timestamp = models.DateTimeField(default=timezone.now)

    nonce = models.PositiveIntegerField(default=0)
    previous_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64)

    class Meta:
        ordering = ["batch", "index"]
        unique_together = ("batch", "index")

    def __str__(self):
        return f"{self.batch.code}#{self.index} {self.event_type}"

    @property
    def event_label(self):
        return self.get_event_type_display()
