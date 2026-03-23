from django.urls import path

import whisper.views as views

urlpatterns = [
    path('whisper', views.whisper_webui, name='whisper_webui'),
    path('', views.homepage, name='homepage'),
    path('api/whisper/<path:model_name>', views.whisper, name='whisper')
]
