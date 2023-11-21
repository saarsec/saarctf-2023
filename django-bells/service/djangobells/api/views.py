
from django.http import HttpRequest, HttpResponse
import time
from api.models import Post
import random
import base64
from api.util.token import Token
from api.util.minixml import miniXML
from django.template import loader


# Create your views here.

def edit(request, post_id, pass_token):
    if localhost(request):
        return HttpResponse("Under Construction")
    return HttpResponse("Forbidden")

def read(request, post_id, pass_token):
    if not localhost(request):
        return HttpResponse("Forbidden")
    try:
        p = Post.objects.values().get(id=post_id)
    except:
        template = loader.get_template('read.html')
        context = {"wish": "Wish not found"}
        return HttpResponse(template.render(context, request))
    if p["pass_token"]==pass_token:
        template = loader.get_template('read.html')
        context = {"wish": p["text"]}
        return HttpResponse(template.render(context, request))
    template = loader.get_template('read.html')
    context = {"wish": "Wrong passtoken"}
    return HttpResponse(template.render(context, request))

def report(request):
    if not localhost(request):
        return HttpResponse("Forbidden")
    if request.method == "GET":
        try:
            if "report" not in request.GET.keys():
                return HttpResponse("GET parameter missing")
            b64 =  request.GET["report"]
            xml = base64.b64decode(b64)
            parser = miniXML(xml.decode("utf-8"))
            parser.parse()
            report_id = parser.get("id")
            report_reason = parser.get("reason")
        except:
            return HttpResponse("Malformed Report")
        send_email_report(report_id, report_reason)
        return HttpResponse(f"Successfully submitted report for: {report_id}")
    return HttpResponse("Forbidden")


def list(request):
    if not localhost(request):
        return HttpResponse("Forbidden")
    posts = Post.objects.all().values()
    json = "{"
    for post in posts:
        json = json + '"' + str(post["id"]) + '"'  + ": " + "{" + '"text": "**********", "stamp": "' + str(post["stamp"]) + '"},'
    json = json[:-1] + "}"
    return HttpResponse(json)

def create(request: HttpRequest):
    if not localhost(request):
        return HttpResponse("Forbidden")
    if request.method == "GET":
        if "post" not in request.GET.keys():
           return HttpResponse("GET parameter missing")
        text =  request.GET["post"]
        stamp = int(time.time())
        nonce = random.randint(0,10**12)
        tok = Token(stamp, nonce).create_token()
        p = Post(pass_token=tok, text=text, stamp=stamp) 
        p.save()
        id = p.id
        return HttpResponse(f'{{"id": "{id}", "token": "{tok}"}}')
    return HttpResponse("Forbidden")

def get_ip(request):
    return request.META.get('REMOTE_ADDR')

def localhost(request):
    return "localhost" == get_ip(request) or "127.0.0.1" == get_ip(request)

def send_email_report(id, reason):
    #TODO
    pass
