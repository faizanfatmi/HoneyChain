from django.contrib import messages
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .blockchain import add_block, verify_chain
from .forms import BatchForm, HiveForm, EventForm
from .models import Batch, Beekeeper, Block, Hive


def home(request):
    stats = {
        "batches": Batch.objects.count(),
        "beekeepers": Beekeeper.objects.count(),
        "hives": Hive.objects.count(),
        "events": Block.objects.count(),
        "kg": Batch.objects.aggregate(t=Sum("quantity_kg"))["t"] or 0,
    }
    recent = Batch.objects.select_related("hive", "hive__beekeeper")[:6]
    return render(request, "index.html", {"stats": stats, "recent": recent})


def verify(request):
    code = (request.GET.get("code") or request.POST.get("code") or "").strip().upper()
    if code:
        if Batch.objects.filter(code=code).exists():
            return redirect("trace", code=code)
        messages.error(request, f"No batch found with code “{code}”.")
    sample_codes = list(Batch.objects.order_by("code").values_list("code", flat=True)[:5])
    return render(request, "verify.html", {"sample_codes": sample_codes})


def trace(request, code):
    batch = get_object_or_404(
        Batch.objects.select_related("hive", "hive__beekeeper"), code=code.upper()
    )
    blocks = list(batch.blocks.order_by("index"))
    verification = verify_chain(batch)
    return render(
        request,
        "trace.html",
        {"batch": batch, "blocks": blocks, "verification": verification},
    )


def dashboard(request):
    batches = Batch.objects.select_related("hive", "hive__beekeeper").annotate(
        blocks_n=Count("blocks")
    )
    context = {
        "batches": batches,
        "beekeepers": Beekeeper.objects.annotate(hive_n=Count("hives")),
        "hives": Hive.objects.select_related("beekeeper"),
        "totals": {
            "batches": batches.count(),
            "kg": Batch.objects.aggregate(t=Sum("quantity_kg"))["t"] or 0,
            "events": Block.objects.count(),
        },
    }
    return render(request, "dashboard.html", context)


def batch_detail(request, code):
    batch = get_object_or_404(Batch, code=code.upper())
    blocks = list(batch.blocks.order_by("index"))
    verification = verify_chain(batch)
    return render(
        request,
        "batch_detail.html",
        {"batch": batch, "blocks": blocks, "verification": verification},
    )


def new_hive(request):
    form = HiveForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        hive = form.save()
        messages.success(request, f"Hive {hive.code} registered.")
        return redirect("dashboard")
    return render(request, "form.html", {"form": form, "title": "Register a hive", "action": "new_hive"})


def new_batch(request):
    form = BatchForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        batch = form.save(commit=False)
        if not batch.code:
            batch.code = _next_batch_code()
        batch.save()
        add_block(batch, event_type=Block.Event.GENESIS, actor="HoneyChain",
                  location="", note="Traceability chain created for this batch.")
        add_block(
            batch,
            event_type=Block.Event.HARVEST,
            actor=str(batch.hive.beekeeper.name),
            location=batch.hive.beekeeper.location,
            note=f"{batch.quantity_kg} kg harvested from hive {batch.hive.code}.",
            data={"floral_source": batch.hive.floral_source},
        )
        messages.success(request, f"Batch {batch.code} created with a fresh chain.")
        return redirect("batch_detail", code=batch.code)
    return render(request, "form.html", {"form": form, "title": "Create a honey batch", "action": "new_batch"})


def add_event(request, code):
    batch = get_object_or_404(Batch, code=code.upper())
    form = EventForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        add_block(
            batch,
            event_type=cd["event_type"],
            actor=cd["actor"],
            location=cd.get("location", ""),
            note=cd.get("note", ""),
            data=form.metrics(),
        )
        _sync_status(batch, cd["event_type"])
        messages.success(request, "New block mined and appended to the chain.")
        return redirect("batch_detail", code=batch.code)
    return render(
        request,
        "form.html",
        {"form": form, "title": f"Add event to {batch.code}", "action": "add_event", "batch": batch},
    )


def api_batch(request, code):
    batch = get_object_or_404(Batch.objects.select_related("hive", "hive__beekeeper"), code=code.upper())
    verification = verify_chain(batch)
    return JsonResponse(
        {
            "batch": {
                "code": batch.code,
                "honey_type": batch.honey_type,
                "quantity_kg": float(batch.quantity_kg),
                "harvest_date": batch.harvest_date.isoformat(),
                "status": batch.get_status_display(),
                "beekeeper": batch.hive.beekeeper.name,
                "apiary_reg_no": batch.hive.beekeeper.apiary_reg_no,
                "hive": batch.hive.code,
                "floral_source": batch.hive.floral_source,
            },
            "verification": verification,
            "chain": [
                {
                    "index": b.index,
                    "event_type": b.event_type,
                    "event_label": b.event_label,
                    "actor": b.actor,
                    "location": b.location,
                    "note": b.note,
                    "data": b.data,
                    "timestamp": b.timestamp.isoformat(),
                    "nonce": b.nonce,
                    "previous_hash": b.previous_hash,
                    "hash": b.hash,
                }
                for b in batch.blocks.order_by("index")
            ],
        },
        json_dumps_params={"indent": 2},
    )


def _next_batch_code():
    from django.utils import timezone

    year = timezone.now().year
    n = Batch.objects.count() + 1
    return f"HNY-{year}-{n:04d}"


_STATUS_BY_EVENT = {
    Block.Event.PROCESSING: Batch.Status.PROCESSING,
    Block.Event.PACKAGING: Batch.Status.PACKAGED,
    Block.Event.TRANSIT: Batch.Status.IN_TRANSIT,
    Block.Event.RETAIL: Batch.Status.ON_SHELF,
    Block.Event.SOLD: Batch.Status.SOLD,
}


def _sync_status(batch, event_type):
    new_status = _STATUS_BY_EVENT.get(event_type)
    if new_status and batch.status != new_status:
        batch.status = new_status
        batch.save(update_fields=["status"])
