from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import OuterRef, Subquery

from login_with_token.views import get_user_from_token


@csrf_exempt
@require_http_methods(["GET"])
def api_branch_licenses(request):
    """GET /api/licenses/  —  header: Authorization: Bearer <token>
    Returns all licenses for the user's assigned branches."""
    user = get_user_from_token(request)
    if not user:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    user_branch_names = list(user.branches.values_list('name', flat=True))

    # ── MOBILE LICENSES ──
    from MobileApp.models import MobileControl, MobileBillingHistory

    latest_payment_sub = MobileBillingHistory.objects.filter(
        control=OuterRef('pk')
    ).order_by('-created_at').values('payment_status')[:1]

    mobile_controls = (
        MobileControl.objects
        .annotate(latest_payment_status=Subquery(latest_payment_sub))
        .select_related('project', 'package', 'active_custom_package', 'shop__branch', 'store')
        .order_by('-updated_date')
    )

    if user_branch_names:
        mobile_controls = mobile_controls.filter(shop__branch__name__in=user_branch_names)

    mobile_licenses = []
    now = timezone.now()
    for c in mobile_controls:
        remaining_days = None
        is_expired = False
        if c.expiry_date:
            delta = c.expiry_date - now
            remaining_days = delta.days
            is_expired = delta.total_seconds() <= 0

        mobile_licenses.append({
            'id': c.id,
            'customer_name': c.customer_name,
            'client_id': c.client_id,
            'license_key': c.license_key,
            'project': c.project.project_name if c.project else None,
            'app_type': c.project.app_type if c.project else None,
            'package': c.package.package_name if c.package else None,
            'custom_package': c.active_custom_package.package_name if c.active_custom_package else None,
            'branch': c.shop.branch.name if c.shop and c.shop.branch else None,
            'store': c.store.name if c.store else None,
            'shop': c.shop.name if c.shop else None,
            'status': c.status,
            'bill_status': c.bill_status,
            'payment_status': getattr(c, 'latest_payment_status', None),
            'login_limit': c.login_limit,
            'registered_devices': c.active_devices.count(),
            'expiry_date': c.expiry_date.isoformat() if c.expiry_date else None,
            'remaining_days': remaining_days,
            'is_expired': is_expired,
            'licence_type': c.licence_type,
            'created_date': c.created_date.isoformat() if c.created_date else None,
        })

    # ── WEB LICENSES ──
    from WebApp.models import WebControl
    web_controls = (
        WebControl.objects
        .select_related('project')
        .order_by('-created_date')
    )

    web_licenses = []
    for c in web_controls:
        web_licenses.append({
            'id': c.id,
            'customer_name': c.customer_name,
            'client_id': c.client_id,
            'project': c.project.project_name if c.project else None,
            'login_limit': c.login_limit,
            'created_date': c.created_date.isoformat() if c.created_date else None,
        })

    return JsonResponse({
        'success': True,
        'user': user.name,
        'branches': user_branch_names,
        'mobile_licenses': mobile_licenses,
        'web_licenses': web_licenses,
        'total_mobile': len(mobile_licenses),
        'total_web': len(web_licenses),
    })
