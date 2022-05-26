from base64 import b64decode

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from phishing.decorators import phish
from phishing.models import Status

PIXEL = b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')


@phish(Status.OPENED)
def opened(request: HttpRequest):
    """Respond with a transparent pixel."""

    return HttpResponse(PIXEL, content_type='image/png')


@phish(Status.CLICKED)
def clicked(request: HttpRequest):
    """Respond with the assigned template."""

    return render(request, f'2.clicked.{request.template}.html')


@phish(Status.PHISHED)
def phished(request: HttpRequest):
    """Respond with a common landing page."""

    return render(request, '3.phished.html')
