from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader


# Create your views here.
def index(request):
    class Question:

        def __init__(self):
            self.id = 0
            self.question_test = ''

    q1 = Question()
    q2 = Question()
    q1.id = 1
    q1.question_text = "Text1"
    q2.id = 2
    q2.question_text = "Text2"

    latest_question_list = [q1, q2]
    template = loader.get_template(
        "controller/templates/controller/index.html")
    context = {
        "latest_question_list": latest_question_list,
    }
    return HttpResponse(template.render(context, request))


def list_projects(request):
    response = request.get('http://http://localhost:8000/projects/')
    # convert reponse data into json
    users = response.json()
    print(users)
    return HttpResponse("Users")
