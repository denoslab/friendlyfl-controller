import os
import requests

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from dotenv import load_dotenv
from django.http import HttpResponseRedirect

from .forms import SiteForm

# take environment variables from .env.
load_dotenv()


# Create your views here.
def index(request):
    # read vars from env
    site_uid = os.getenv('SITE_UID')
    router_url = os.getenv('ROUTER_URL')
    router_username = os.getenv('ROUTER_USERNAME')
    router_password = os.getenv('ROUTER_PASSWORD')

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        site_form = SiteForm(request.POST)
        # check if form is valid:
        if site_form.is_valid():
            site_name = site_form.cleaned_data['name']
            site_description = site_form.cleaned_data['description']
            response = requests.get('{0}/sites/lookup?uid={1}'.format(router_url, site_uid),
                                    auth=(router_username, router_password))
            site_list = response.json()
            if len(site_list) > 0:
                # site already exists
                current_site = site_list[0]
                if 'deregister_site' in request.POST:
                    # delete site with DELETE
                    requests.delete('{0}/sites/{1}/'.format(router_url, current_site['id']),
                                    auth=(router_username, router_password))
                else:
                    # update site with PUT
                    current_site['name'] = site_name
                    current_site['description'] = site_description
                    requests.put('{0}/sites/{1}/'.format(router_url, current_site['id']),
                                 auth=(router_username, router_password),
                                 data=current_site)
            else:
                # site does not exist, create site with POST
                current_site = dict()
                current_site['uid'] = site_uid
                current_site['name'] = site_name
                current_site['description'] = site_description
                # register new site
                requests.post('{0}/sites/'.format(router_url),
                              auth=(router_username, router_password),
                              data=current_site)
                # redirect to a new URL:
            return HttpResponseRedirect("./")

    # if a GET, load the form
    else:
        response = requests.get('{0}/sites/lookup?uid={1}'.format(router_url, site_uid),
                                auth=(router_username, router_password))
        site_list = response.json()
        current_site = None

        if len(site_list) > 0:
            # site already exists, init form with existing values
            current_site = site_list[0]
            site_form = SiteForm(initial={
                'name': current_site['name'],
                'description': current_site['description'],
            })
        else:
            # site does not exist, init blank form
            site_form = SiteForm()

        # render template
        template = loader.get_template(
            "controller/index.html")
        context = {
            # built-in uid of site
            "site_uid": site_uid,
            # if available, current site info from router
            "site_detail": current_site,
            # site form
            "site_form": site_form,
        }
        return HttpResponse(template.render(context, request))
