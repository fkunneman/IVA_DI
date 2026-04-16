from django.urls import path

import langchain.views as views

urlpatterns = [
    path('langchain', views.langchain_webui, name='langchain_webui'),
    path('langchain/new_session', views.new_session, name='new_session'),
    path('langchain/manage-sessions', views.manage_sessions, name='manage_sessions'),
    path('api/langchain/new-session/<path:model_name>', views.api_new_session, name='api_new_session'),
    path('api/langchain/message/<str:agent_id>', views.api_message, name='api_message'),
]
