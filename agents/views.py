import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import Agent, AgentReferral


def _clean(value):
    return (value or '').strip()


def _validate(name, code, number, company_name, exclude_pk=None):
    """Return a list of validation errors for the submitted agent fields."""
    errors = []

    if not name:
        errors.append('Name is required.')

    if not code:
        errors.append('Code is required.')
    else:
        duplicates = Agent.objects.filter(code__iexact=code)
        if exclude_pk:
            duplicates = duplicates.exclude(pk=exclude_pk)
        if duplicates.exists():
            errors.append(f'The code "{code}" is already used by another agent.')

    if not number:
        errors.append('Number is required.')

    if not company_name:
        errors.append('Company name is required.')

    # Same agent name is allowed in other companies, but not twice in one company
    if name and company_name:
        duplicates = Agent.objects.filter(
            name__iexact=name,
            company_name__iexact=company_name,
        )
        if exclude_pk:
            duplicates = duplicates.exclude(pk=exclude_pk)
        if duplicates.exists():
            errors.append(
                f'The agent "{name}" already exists for company "{company_name}".'
            )

    return errors


def agent_list(request):
    query = _clean(request.GET.get('q'))

    agents = (
        Agent.objects
        .annotate(referral_total=Count('referrals'))
        .prefetch_related('referrals')
    )
    if query:
        agents = agents.filter(
            Q(name__icontains=query)
            | Q(code__icontains=query)
            | Q(number__icontains=query)
            | Q(company_name__icontains=query)
            | Q(referral_code__icontains=query)
        )

    return render(request, 'agents/agents_list.html', {
        'agents': agents,
        'query': query,
    })


def agent_add(request):
    if request.method != 'POST':
        return redirect('agents:agent_list')

    name = _clean(request.POST.get('name'))
    code = _clean(request.POST.get('code'))
    number = _clean(request.POST.get('number'))
    company_name = _clean(request.POST.get('company_name'))

    errors = _validate(name, code, number, company_name)
    if errors:
        for error in errors:
            messages.error(request, error)
        return redirect('agents:agent_list')

    # Referral code is generated automatically inside Agent.save()
    agent = Agent(name=name, code=code, number=number, company_name=company_name)
    agent.save()

    messages.success(
        request,
        f'Agent "{agent.name}" created with referral code {agent.referral_code}.'
    )
    return redirect('agents:agent_list')


def agent_edit(request, pk):
    agent = get_object_or_404(Agent, pk=pk)

    if request.method != 'POST':
        return redirect('agents:agent_list')

    name = _clean(request.POST.get('name'))
    code = _clean(request.POST.get('code'))
    number = _clean(request.POST.get('number'))
    company_name = _clean(request.POST.get('company_name'))

    errors = _validate(name, code, number, company_name, exclude_pk=agent.pk)
    if errors:
        for error in errors:
            messages.error(request, error)
        return redirect('agents:agent_list')

    # Referral code is intentionally NOT touched here – it stays as created
    agent.name = name
    agent.code = code
    agent.number = number
    agent.company_name = company_name
    agent.save()

    messages.success(request, f'Agent "{agent.name}" updated.')
    return redirect('agents:agent_list')


def agent_delete(request, pk):
    agent = get_object_or_404(Agent, pk=pk)

    if request.method == 'POST':
        name = agent.name
        agent.delete()
        messages.success(request, f'Agent "{name}" deleted.')

    return redirect('agents:agent_list')


def _api_payload(request):
    """Return the submitted body as a dict, accepting JSON or form data."""
    if 'application/json' in (request.content_type or ''):
        try:
            payload = json.loads(request.body or b'{}')
        except (TypeError, ValueError):
            return None
        return payload if isinstance(payload, dict) else None
    return request.POST


@csrf_exempt
def api_agent_referral(request):
    """Public API used by external forms to register a customer mail id.

    POST http://127.0.0.1:8000/agents/api/agent-referral/
    Content-Type: application/json
        {"mail_id": "customer@example.com", "referral_code": "AG-7K2M9Q"}

    The referral code must belong to an existing agent, otherwise nothing
    is stored and a 400 response is returned.
    """
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'error': 'Only POST is allowed.'},
            status=405,
        )

    payload = _api_payload(request)
    if payload is None:
        return JsonResponse(
            {'success': False, 'error': 'Invalid JSON body.'},
            status=400,
        )

    mail_id = _clean(payload.get('mail_id'))
    referral_code = _clean(payload.get('referral_code'))

    errors = []
    if not mail_id:
        errors.append('mail_id is required.')
    else:
        try:
            validate_email(mail_id)
        except ValidationError:
            errors.append('mail_id must be a valid email address.')

    agent = None
    if not referral_code:
        errors.append('referral_code is required.')
    else:
        agent = Agent.objects.filter(referral_code__iexact=referral_code).first()
        if agent is None:
            errors.append(f'Invalid referral code "{referral_code}".')

    if errors:
        return JsonResponse(
            {'success': False, 'error': errors[0], 'errors': errors},
            status=400,
        )

    referral = AgentReferral.objects.filter(
        agent=agent,
        mail_id__iexact=mail_id,
    ).first()
    created = False
    if referral is None:
        try:
            referral = AgentReferral.objects.create(agent=agent, mail_id=mail_id)
            created = True
        except IntegrityError:
            # Same mail id was inserted by a parallel request in the meantime
            referral = AgentReferral.objects.get(
                agent=agent,
                mail_id__iexact=mail_id,
            )

    if created:
        message = f'Mail id "{referral.mail_id}" registered for agent "{agent.name}".'
    else:
        message = (
            f'Mail id "{referral.mail_id}" was already registered '
            f'for agent "{agent.name}".'
        )

    return JsonResponse({
        'success': True,
        'message': message,
        'already_registered': not created,
        'data': {
            'id': referral.id,
            'mail_id': referral.mail_id,
            'submitted_at': referral.created_at.isoformat(),
            'agent': {
                'id': agent.id,
                'name': agent.name,
                'code': agent.code,
                'company_name': agent.company_name,
                'referral_code': agent.referral_code,
            },
        },
    }, status=201 if created else 200)
