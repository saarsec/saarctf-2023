from django.shortcuts import render 
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from djangobells.settings import make_api_call, make_api_call_params, make_api_call_token
import json
from django.template import loader
from urllib.parse import quote
import base64
import re 


def get_post(request, post_id, pass_token):
    res = make_api_call_token(request, "read", post_id, pass_token)
    return HttpResponse(res) 


def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render())

def create(request: HttpRequest):
    if "" == request.GET.get("post_data", ""):
        return HttpResponse("Missing post_data parameter")
    res = make_api_call_params(request, "create", "post=" + request.GET["post_data"])
    try:
        data = json.loads(res)
        id = data["id"]
        token = data["token"]
        return HttpResponseRedirect(f"/read/{id}/{token}")
    except:
        return HttpResponse("Malformed Statement")

def list_html(request: HttpRequest):
    res = make_api_call(request, "list")
    data = list(json.loads(res).items())
    template = loader.get_template('list.html')
    context = {"wishes": data}
    return HttpResponse(template.render(context,request))

def report(request: HttpRequest):
    if "" == request.GET.get("id", ""):
        return HttpResponse("Missing id parameter")
    id = request.GET["id"]
    try:
        pattern = re.compile(r"^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$")
        if pattern.fullmatch(id) == None:
            raise ValueError
        xml = f'<?xml version="1.0" ?>\n<report>\n<id>{id}</id>\n<reason>This post was submitted for inspection</reason>\n</report>'
        xml_base64 = base64.b64encode(xml.encode('utf-8'))
        xml_url_encoded = quote(quote(xml_base64.decode('utf-8')))
        res = make_api_call_params(request, "report", "report=" + xml_url_encoded)
        if not "Successfully" in res:
            raise ConnectionError
    except:
        return HttpResponse("Could not submit report")
    return HttpResponse("Thanks for submitting a report")
