import os
import requests

from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect
from dotenv import load_dotenv
from django.http import HttpResponseRedirect
import logging
import json

from .forms import SiteForm, ProjectJoinForm, ProjectNewForm, ProjectLeaveForm

# take environment variables from .env.
load_dotenv()
logger = logging.getLogger(__name__)

# read vars from env
site_uid = os.getenv('SITE_UID')
router_url = os.getenv('ROUTER_URL')
router_username = os.getenv('ROUTER_USERNAME')
router_password = os.getenv('ROUTER_PASSWORD')


# Create your views here.
def index(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        site_form = SiteForm(request.POST)
        # check if form is valid:
        if site_form.is_valid():
            site_name = site_form.cleaned_data['name']
            site_description = site_form.cleaned_data['description']
            # get current site info
            response = requests.get('{0}/sites/lookup/?uid={1}'.format(router_url, site_uid),
                                    auth=(router_username, router_password))
            current_site = None
            if response.ok:
                current_site = response.json()

            if current_site:
                # site already exists
                if 'deregister_site' in request.POST:
                    # delete site with DELETE
                    requests.delete('{0}/sites/{1}/'.format(router_url, current_site['id']),
                                    auth=(router_username, router_password))
                else:
                    # update site with PUT
                    current_site['name'] = site_name
                    current_site['description'] = site_description
                    requests.put('{0}/sites/{1}/'.format(router_url, current_site['id']),
                                 headers={'Content-Type': 'application/json'},
                                 auth=(router_username, router_password),
                                 data=json.dumps(current_site))
            else:
                # site does not exist, create site with POST
                current_site = dict()
                current_site['uid'] = site_uid
                current_site['name'] = site_name
                current_site['description'] = site_description
                # register new site
                requests.post('{0}/sites/'.format(router_url),
                              headers={'Content-Type': 'application/json'},
                              auth=(router_username, router_password),
                              data=json.dumps(current_site))
        # redirect to the same page
        return HttpResponseRedirect("./")
    # if a GET, load the form
    else:
        response = requests.get('{0}/sites/lookup/?uid={1}'.format(router_url, site_uid),
                                auth=(router_username, router_password))
        # if current site exists, store it for use
        current_site = None
        if response.ok:
            current_site = response.json()

        project_participants = None

        if current_site:
            # site already exists, init form with existing values
            site_form = SiteForm(initial={
                'name': current_site['name'],
                'description': current_site['description'],
            })
            # get all projects this site is involved
            response_project_participants = requests \
                .get('{0}/projects/lookup/?site_id={1}'.format(router_url, current_site['id']),
                     auth=(router_username, router_password))
            project_participants = response_project_participants.json()
        else:
            # site does not exist, init blank form
            site_form = SiteForm()

        project_leave_form = ProjectLeaveForm()
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
            # project leave form
            "project_leave_form": project_leave_form,
            # projects the site is involved
            "project_participants": project_participants,
        }
        return HttpResponse(template.render(context, request))


def project_leave(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        project_leave_form = ProjectLeaveForm(request.POST)
        # check if form is valid:
        print(project_leave_form)
        if project_leave_form.is_valid():
            pp_id = project_leave_form.cleaned_data['participant_id']
            # get current site info
            rr = requests.delete('{0}/project-participants/{1}/'.format(router_url, pp_id),
                                 auth=(router_username, router_password))
            print(rr)
    return redirect('index')


def project_new(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        project_new_form = ProjectNewForm(request.POST)

        # check if form is valid:
        if project_new_form.is_valid():
            project_name = project_new_form.cleaned_data['name']
            description = project_new_form.cleaned_data['description']
            tasks = project_new_form.cleaned_data['tasks']
            # get current site info
            response = requests.get('{0}/sites/lookup/?uid={1}'.format(router_url, site_uid),
                                    auth=(router_username, router_password))
            current_site = None
            if response.ok:
                current_site = response.json()

            if current_site:
                # create new Project
                project = dict()
                project['name'] = project_name
                project['description'] = description
                project['site'] = current_site['id']
                project['tasks'] = []
                requests.post('{0}/projects/'.format(router_url),
                              headers={'Content-Type': 'application/json'},
                              auth=(router_username, router_password),
                              data=json.dumps(project))
        # redirect to the home page
        return HttpResponseRedirect("/controller/")
    # if a GET, load the form
    else:
        project_new_form = ProjectNewForm(initial={'tasks': '{}'})
    # render template
    template = loader.get_template(
        "controller/project_new.html")
    context = {
        "project_new_form": project_new_form,
    }
    return HttpResponse(template.render(context, request))


def project_join(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        project_join_form = ProjectJoinForm(request.POST)
        # check if form is valid:
        if project_join_form.is_valid():
            project_name = project_join_form.cleaned_data['name']
            notes = project_join_form.cleaned_data['notes']
            response = requests.get('{0}/projects/lookup/?name={1}'.format(router_url, project_name),
                                    auth=(router_username, router_password))
            project_to_join = None
            if response.ok:
                project_to_join = response.json()
            # retrieve site info
            response = requests.get('{0}/sites/lookup/?uid={1}'.format(router_url, site_uid),
                                    auth=(router_username, router_password))
            current_site = None
            if response.ok:
                current_site = response.json()
            if project_to_join:
                # create new ProjectParticipant to join the project
                project_participant = dict()
                project_participant['site'] = current_site['id']
                project_participant['project'] = project_to_join['id']
                project_participant['role'] = 'PA'
                project_participant['notes'] = notes
                requests.post('{0}/project-participants/'.format(router_url),
                              headers={'Content-Type': 'application/json'},
                              auth=(router_username, router_password),
                              data=json.dumps(project_participant))
        # redirect to the home page
        return HttpResponseRedirect("/controller/")
    # if a GET, load the form
    else:
        # site does not exist, init blank form
        project_join_form = ProjectJoinForm()

    # render template
    template = loader.get_template(
        "controller/project_join.html")
    context = {
        "project_join_form": project_join_form,
    }
    return HttpResponse(template.render(context, request))


def project_detail(request, project_id, site_id):
    project_response = requests.get('{0}/projects/{1}/'.format(router_url, project_id),
                                    auth=(router_username, router_password))
    current_project = None
    all_participants = None
    all_runs = None
    if project_response.ok:
        current_project = project_response.json()
        if site_id == current_project["site"]:
            participants_response = requests.get('{0}/project-participants/lookup/?project={1}'.format(router_url, project_id),
                                                 auth=(router_username, router_password))
            if participants_response.ok:
                all_participants = participants_response.json()

    runs_response = requests.get('{0}/runs/lookup/?project={1}'.format(router_url, project_id),
                                 auth=(router_username, router_password))
    if runs_response.ok:
        all_runs = runs_response.json()
    # render template
    template = loader.get_template(
        "controller/project_detail.html")
    context = {
        "project_id": project_id,
        "project_details": current_project,
        "participants": all_participants,
        "site_id": site_id,
        "runs": all_runs
    }
    return HttpResponse(template.render(context, request))


def run_detail(request, batch, project_id, site_id):
    runs_response = requests.get(
        '{0}/runs/detail/?batch={1}&project={2}&site={3}'.format(
            router_url, batch, project_id, site_id),
        auth=(router_username, router_password))
    # if current site exists, store it for use
    dic = {}
    if runs_response.ok:
        dic = runs_response.json()
    # run participants
    # render template
    template = loader.get_template(
        "controller/run_detail.html")
    context = {
        "runs": dic['runs'] if dic else [],
        "participant": dic['participant'] if dic else -1
    }
    return HttpResponse(template.render(context, request))
