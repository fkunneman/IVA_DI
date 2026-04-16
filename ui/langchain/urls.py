from django.urls import path

import langchain.views as views

urlpatterns = [
    path('langchain', views.langchain_webui, name='langchain_webui'),
    path('langchain/new_session', views.new_session, name='new_session'),
    path('langchain/manage-sessions', views.manage_sessions, name='manage_sessions'),
    # path('api/whisper/<path:model_name>', views.whisper, name='whisper')
]
