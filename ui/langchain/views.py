import json
import uuid
from pathlib import Path

import torch
from django import urls
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from torch import OutOfMemoryError

from .agents import agents, create_agent, histories, Message, discard_agent
from .forms import NewSessionForm, MessageForm, SessionsForm


def langchain_webui(request: HttpRequest) -> HttpResponse:
    has_expired = False
    new_session_form = NewSessionForm(None)
    log_url = None

    # Use existing session if available, otherwise "no session"
    agent_id = request.session.get('agent_id', None)
    agent = agents.get(agent_id)
    if agent is None:
        if agent_id:
            # There was an agent ID in the session but it does not exist anymore or application has restarted
            has_expired = True
        history = None
    else:
        assert isinstance(agent_id, str)
        history = histories[agent_id]
        log_filename = Path(agent.logfile).name
        log_url = '/logs/' + log_filename

    if request.method == 'POST' and agent is not None:
        message_form = MessageForm(request.POST)
        if message_form.is_valid():
            message = message_form.cleaned_data['message']
            print(f"Taking message: {message}")
            history.append(Message(message, "person"))
            response = agent.chat_with_agent(message)
            print(f"Response: {response}")
            history.append(Message(response, "agent"))
            # Redirect to self to clear POST data
            return redirect('langchain_webui')
    else:
        message_form = MessageForm()

    return render(request, "langchain/index.html", {
        'agent_id': agent_id,
        'agent': agent,
        'history': history,
        'new_session_form': new_session_form,
        'message_form': message_form,
        'has_expired': has_expired,
        'log_url': log_url,
        'out_of_memory': 'error' in request.GET and request.GET['error'] == 'out_of_memory'
    })


def new_session(request: HttpRequest) -> HttpResponse:
    new_session_form = NewSessionForm(request.POST or None)
    if request.method == 'POST' and new_session_form.is_valid():
        # Create a new session
        agent_id = str(uuid.uuid4())
        try:
            agent = create_agent(new_session_form.cleaned_data['model_name'], agent_id)
        except OutOfMemoryError:
            return redirect(urls.reverse('langchain_webui') + '?error=out_of_memory')
        agents[agent_id] = agent
        # Add first message
        histories[agent_id].append(Message(agent.patterns[0], "agent"))
        request.session['agent_id'] = agent_id
        return redirect('langchain_webui')
    else:
        raise Exception("Invalid form")


def manage_sessions(request: HttpRequest) -> HttpResponse:
    cuda_summary = torch.cuda.memory_summary() if torch.cuda.is_available() else "CUDA niet beschikbaar"
    form = SessionsForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        agent_id = form.cleaned_data['session']
        discard_agent(agent_id)
        return redirect('manage_sessions')
    return render(request, "langchain/manage_sessions.html", {
        'sessions': agents.keys(),
        'cuda_summary': cuda_summary,
        'form': form,
    })


@csrf_exempt
def api_new_session(request: HttpRequest, model_name: str) -> HttpResponse:
    agent_id = str(uuid.uuid4()) + '-API'
    try:
        agent = create_agent(model_name, agent_id)
    except OutOfMemoryError:
        return HttpResponse(
            json.dumps({
                'error': 'out of memory',
            }),
            content_type='application/json',
            status=500
        )
    agents[agent_id] = agent
    histories[agent_id].append(Message(agent.patterns[0], "agent"))
    request.session['agent_id'] = agent_id
    print(f"Created new session (API): {agent_id}")
    return HttpResponse(
        json.dumps({
            'agent_id': agent_id,
            'first_message': agent.patterns[0],
        }),
        content_type='application/json',
    )


@csrf_exempt
def api_message(request: HttpRequest, agent_id: str) -> HttpResponse:
    try:
        agent = agents[agent_id]
    except KeyError:
        return HttpResponse(
            json.dumps({
                'error': 'invalid agent id',
            }),
            content_type='application/json',
            status=400
        )
    history = histories[agent_id]
    message = request.POST['message']
    print(f"Taking message (API): {message}")
    history.append(Message(message, "person"))
    response = agent.chat_with_agent(message)
    print(f"Response (API): {response}")
    history.append(Message(response, "agent"))
    return HttpResponse(
        json.dumps({
            'response': response,
        })
    )

