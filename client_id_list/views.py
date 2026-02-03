from django.http import JsonResponse
from StoreShop.models import Shop  # import Shop model

def get_client_ids(request):
    """
    API:
    Returns all client IDs with company name and place
    """

    shops = Shop.objects.filter(is_active=True).select_related('store')

    data = []

    for shop in shops:
        data.append({
            "client_id": shop.client_id,
            "company_name": shop.name,     # Shop name = company
            "place": shop.place
        })

    return JsonResponse({
        "status": True,
        "count": len(data),
        "data": data
    })