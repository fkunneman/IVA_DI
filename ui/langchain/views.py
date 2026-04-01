import uuid

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect

from .agents import agents, create_agent, histories, Message
from .forms import NewSessionForm, MessageForm


def langchain_webui(request: HttpRequest) -> HttpResponse:
    has_expired = False
    new_session_form = NewSessionForm(None)

    # Use existing session if available, otherwise "no session"
    agent_id = request.session.get('agent_id', None)
    assert isinstance(agent_id, str)
    agent = agents.get(agent_id)
    if agent is None:
        agent_id = None  # Session has expired
        has_expired = True
        history = None
    else:
        history = histories[agent_id]

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
    })


def new_session(request: HttpRequest) -> HttpResponse:
    new_session_form = NewSessionForm(request.POST or None)
    if request.method == 'POST' and new_session_form.is_valid():
        # Create a new session
        agent = create_agent(new_session_form.cleaned_data['model_name'])
        agent_id = str(uuid.uuid4())
        agents[agent_id] = agent
        # Add first message
        histories[agent_id].append(Message(agent.patterns[0], "agent"))
        request.session['agent_id'] = agent_id
        return redirect('langchain_webui')
    else:
        raise Exception("Invalid form")
