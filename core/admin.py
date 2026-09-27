from django.contrib import admin

from .models import Batch, Beekeeper, Block, Hive


@admin.register(Beekeeper)
class BeekeeperAdmin(admin.ModelAdmin):
    list_display = ("name", "apiary_reg_no", "location", "state", "certified_organic")
    search_fields = ("name", "apiary_reg_no", "location")


@admin.register(Hive)
class HiveAdmin(admin.ModelAdmin):
    list_display = ("code", "beekeeper", "floral_source", "installed_on")
    search_fields = ("code", "floral_source")
    list_filter = ("floral_source",)


class BlockInline(admin.TabularInline):
    model = Block
    extra = 0
    readonly_fields = ("index", "event_type", "actor", "hash", "previous_hash", "nonce", "timestamp")
    ordering = ("index",)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("code", "honey_type", "hive", "quantity_kg", "status", "created_at")
    search_fields = ("code", "honey_type")
    list_filter = ("status",)
    inlines = [BlockInline]


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("batch", "index", "event_type", "actor", "timestamp")
    search_fields = ("batch__code", "actor", "hash")
    list_filter = ("event_type",)
