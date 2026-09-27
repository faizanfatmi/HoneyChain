from django.contrib.messages import get_messages
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def url(name, *args, **kwargs):
    return reverse(name, args=args or None, kwargs=kwargs or None)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        "static": static,
        "url": url,
        "get_messages": get_messages,
    })
    env.filters.update({
        "short_hash": lambda h: (h[:10] + "…" + h[-6:]) if h and len(h) > 18 else h,
    })
    return env
