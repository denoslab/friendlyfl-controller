from django import template

register = template.Library()


@register.filter
def last_status_value(runs):
    if len(runs) == 0:
        return 'NULL'
    return runs[-1].get('status')
