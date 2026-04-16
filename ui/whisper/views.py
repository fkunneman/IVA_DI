import tempfile

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from whisper.forms import WhisperForm


def whisper_webui(request: HttpRequest) -> HttpResponse:
    transcription = None
    if request.method == "POST":
        form = WhisperForm(request.POST, request.FILES)
        if form.is_valid():
            from whisper.whisper import transcribe
            with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
                fp.write(request.FILES['audio_file'].read())
                fp.close()
                transcription = transcribe(form.cleaned_data['model_name'], fp.name)
    else:
        form = WhisperForm()
    return render(request, "whisper/index.html", {
        'form': form,
        'transcription': transcription,
    })


def homepage(request: HttpRequest) -> HttpResponse:
    return render(request, "whisper/homepage.html")


@csrf_exempt
def whisper(request: HttpRequest, model_name: str) -> HttpResponse:
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    f = request.FILES['file']

    from whisper.whisper import transcribe
    with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
        fp.write(f.read())
        fp.close()
        transcription = transcribe(model_name, fp.name)
        response = HttpResponse(transcription)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

