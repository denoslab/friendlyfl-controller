import arrow

from django import template

register = template.Library()

update_at = 'updated_at'
create_at = 'created_at'
status_dic = {"FAILED": 0, "PENDING FAILED": 1, "STANDBY": 2, "PREPARING": 3, "RUNNING": 4, "PENDING SUCCESS": 5,
              "SUCCESS": 6}
download = 'download'
restart = 'restart'
stop = 'stop'


@register.filter
def last_status_value(runs):
    if len(runs) == 0:
        return 'NULL'
    return runs[-1].get('status')


@register.filter
def last_run_duration(runs):
    if len(runs) == 0:
        return 0
    update_at_str = runs[-1].get(update_at)
    create_at_str = runs[-1].get(create_at)
    total_seconds = get_time_diff(update_at_str, create_at_str)
    days = total_seconds.days
    hours, remainder = divmod(total_seconds.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days} days  {hours} hrs {minutes} mins  {seconds} secs"


@register.filter
def site_duration(site):
    if not site:
        return 0
    update_at_str = site.get(update_at)
    create_at_str = site.get(create_at)
    total_seconds = get_time_diff(update_at_str, create_at_str)
    hours = total_seconds.seconds // 3600
    minutes = (total_seconds.seconds // 60) % 60
    seconds = total_seconds.seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_time_diff(update_at_str, create_at_str):
    if not update_at_str or not create_at_str:
        return 0
    update_at = arrow.get(update_at_str[:-1])
    create_at = arrow.get(create_at_str[:-1])
    if not update_at or not create_at:
        return 0
    return update_at - create_at


@register.filter
def get_actions(status: str):
    actions = []
    if not status:
        return actions
    status = status.upper()
    if status not in status_dic:
        return actions
    code = status_dic[status]
    if code == 6:
        actions.append(download)
        actions.append(restart)
        return actions
    if code >= 2:
        actions.append(stop)
        actions.append(restart)
        return actions
    actions.append(restart)
    return actions


@register.filter
def upper_first_char(status: str):
    if not status:
        return ''
    return status[:1].upper() + status[1:]
