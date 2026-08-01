from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from Lisence_Mobile_App.login_with_token.views import get_user_from_token
from StoreShop.models import Shop


@csrf_exempt
@require_http_methods(["GET"])
def api_customers(request):
    """GET /api/customers/  —  header: Authorization: Bearer <token>
    Returns all customers (companies) with full company and corporate details,
    filtered to the user's assigned branches only."""
    user = get_user_from_token(request)
    if not user:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    user_branch_names = list(user.branches.values_list('name', flat=True))

    shops = (
        Shop.objects
        .select_related('store', 'branch', 'store__branch')
        .order_by('name')
    )
    if user_branch_names:
        shops = shops.filter(branch__name__in=user_branch_names)

    customers = []
    for shop in shops:
        store = shop.store
        customers.append({
            'customer_id': shop.id,
            'client_id': shop.client_id,
            'company_name': shop.name,
            'company_place': shop.place,
            'company_email': shop.email,
            'company_contact_no': shop.contact_no,
            'country': shop.country,
            'currency_code': shop.currency_code,
            'is_active': shop.is_active,
            'branch': shop.branch.name if shop.branch else None,
            'created_date': shop.created_at.isoformat() if shop.created_at else None,
            'corporate': {
                'corporate_id': store.store_id if store else None,
                'corporate_name': store.name if store else None,
                'corporate_place': store.place if store else None,
                'corporate_branch': store.branch.name if store and store.branch else None,
            },
        })

    return JsonResponse({
        'success': True,
        'user': user.name,
        'branches': user_branch_names,
        'total': len(customers),
        'data': customers,
    })
