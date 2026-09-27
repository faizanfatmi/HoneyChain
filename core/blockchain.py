import hashlib
import json
from datetime import timezone as _timezone

from django.conf import settings

GENESIS_PREV_HASH = "0" * 64


def _canonical_timestamp(timestamp):
    if hasattr(timestamp, "isoformat"):
        if getattr(timestamp, "tzinfo", None) is not None:
            timestamp = timestamp.astimezone(_timezone.utc)
        return timestamp.isoformat()
    return str(timestamp)


def _canonical_payload(*, index, event_type, actor, location, note, data, timestamp, previous_hash, nonce):
    payload = {
        "index": index,
        "event_type": event_type,
        "actor": actor,
        "location": location,
        "note": note,
        "data": data,
        "timestamp": _canonical_timestamp(timestamp),
        "previous_hash": previous_hash,
        "nonce": nonce,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def compute_hash(*, index, event_type, actor, location, note, data, timestamp, previous_hash, nonce):
    raw = _canonical_payload(
        index=index,
        event_type=event_type,
        actor=actor,
        location=location,
        note=note,
        data=data,
        timestamp=timestamp,
        previous_hash=previous_hash,
        nonce=nonce,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def mine(*, index, event_type, actor, location, note, data, timestamp, previous_hash, difficulty=None):
    if difficulty is None:
        difficulty = getattr(settings, "HONEYCHAIN_DIFFICULTY", 4)
    target = "0" * difficulty
    nonce = 0
    while True:
        h = compute_hash(
            index=index,
            event_type=event_type,
            actor=actor,
            location=location,
            note=note,
            data=data,
            timestamp=timestamp,
            previous_hash=previous_hash,
            nonce=nonce,
        )
        if h.startswith(target):
            return nonce, h
        nonce += 1


def hash_of_block(block):
    return compute_hash(
        index=block.index,
        event_type=block.event_type,
        actor=block.actor,
        location=block.location,
        note=block.note,
        data=block.data,
        timestamp=block.timestamp,
        previous_hash=block.previous_hash,
        nonce=block.nonce,
    )


def add_block(batch, *, event_type, actor, location="", note="", data=None, timestamp=None):
    from django.utils import timezone

    from .models import Block

    data = data or {}
    timestamp = timestamp or timezone.now()

    last = batch.blocks.order_by("-index").first()
    if last is None:
        index = 0
        previous_hash = GENESIS_PREV_HASH
    else:
        index = last.index + 1
        previous_hash = last.hash

    nonce, h = mine(
        index=index,
        event_type=event_type,
        actor=actor,
        location=location,
        note=note,
        data=data,
        timestamp=timestamp,
        previous_hash=previous_hash,
    )
    return Block.objects.create(
        batch=batch,
        index=index,
        event_type=event_type,
        actor=actor,
        location=location,
        note=note,
        data=data,
        timestamp=timestamp,
        nonce=nonce,
        previous_hash=previous_hash,
        hash=h,
    )


def verify_chain(batch):
    blocks = list(batch.blocks.order_by("index"))
    expected_prev = GENESIS_PREV_HASH

    for block in blocks:
        if block.previous_hash != expected_prev:
            return {
                "valid": False,
                "length": len(blocks),
                "broken_at": block.index,
                "reason": f"Block #{block.index} points to the wrong previous hash.",
            }
        if hash_of_block(block) != block.hash:
            return {
                "valid": False,
                "length": len(blocks),
                "broken_at": block.index,
                "reason": f"Block #{block.index} contents were altered (hash mismatch).",
            }
        expected_prev = block.hash

    return {
        "valid": True,
        "length": len(blocks),
        "broken_at": None,
        "reason": "All blocks are intact and correctly linked.",
    }
