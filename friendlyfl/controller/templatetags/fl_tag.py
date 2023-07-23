from django import template

register = template.Library()


@register.filter
def last_status_value(runs):
    return runs[-1].get('status')
