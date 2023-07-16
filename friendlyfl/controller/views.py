import os
import requests

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from dotenv import load_dotenv

# take environment variables from .env.
load_dotenv()


# Create your views here.
def index(request):

    # read vars from env
    site_uid = os.getenv('SITE_UID')
    router_url = os.getenv('ROUTER_URL')
    router_username = os.getenv('ROUTER_USERNAME')
    router_password = os.getenv('ROUTER_PASSWORD')

    response = requests.get('{0}/sites/lookup?uid={1}'.format(router_url, site_uid),
                            auth=(router_username, router_password))
    site_list = response.json()

    # render template
    template = loader.get_template(
        "controller/index.html")
    context = {
        # built-in uid of site
        "site_uid": site_uid,
        # if available, site info from router
        "site_detail": site_list[0] if len(site_list) > 0 else None,
    }
    return HttpResponse(template.render(context, request))

