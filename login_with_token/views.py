from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from app1.models import Users
from .models import ApiToken


def get_user_from_token(request):
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Bearer '):
        return None
    token_str = auth.split(' ', 1)[1].strip()
    try:
        api_token = ApiToken.objects.select_related('user').get(token=token_str, is_active=True)
        if api_token.user.is_active:
            return api_token.user
    except ApiToken.DoesNotExist:
        pass
    return None


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """POST /api/auth/login/  —  {"email": "...", "password": "..."}"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return JsonResponse({'success': False, 'error': 'Email and password are required'}, status=400)

    try:
        user = Users.objects.get(email=email)
    except Users.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

    if user.password != password:
        return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

    if not user.is_active:
        return JsonResponse({'success': False, 'error': 'Account is deactivated'}, status=403)

    ApiToken.objects.filter(user=user).update(is_active=False)
    api_token = ApiToken.objects.create(user=user)

    branches = list(user.branches.values('id', 'name', 'place', 'country', 'currency_code', 'auto_cut'))

    return JsonResponse({
        'success': True,
        'token': api_token.token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'level': user.level,
            'user_role': user.user_role,
            'branches': branches,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """POST /api/auth/logout/  —  header: Authorization: Bearer <token>"""
    user = get_user_from_token(request)
    if not user:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    auth = request.META.get('HTTP_AUTHORIZATION', '')
    token_str = auth.split(' ', 1)[1].strip()
    ApiToken.objects.filter(user=user, token=token_str).update(is_active=False)

    return JsonResponse({'success': True, 'message': 'Logged out successfully'})
