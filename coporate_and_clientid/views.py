from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from StoreShop.models import Store, Shop
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from MobileApp.models import MobileControl

@api_view(['GET'])
@renderer_classes([JSONRenderer])
def corporate_and_clientid_list(request):
    """
    Returns corporates (stores) with their shops, client_ids,
    and related mobile project names
    """

    data = []

    stores = Store.objects.all().prefetch_related('shop_set')

    for store in stores:
        shops_data = []

        shops = Shop.objects.filter(store=store)

        for shop in shops:
            # 🔹 Get all project names linked to this client_id
            projects = (
                MobileControl.objects
                .filter(client_id=shop.client_id)
                .select_related('project')
                .values_list('project__project_name', flat=True)
                .distinct()
            )

            shops_data.append({
                "shop_name": shop.name,
                "client_id": shop.client_id,
                "projects": list(projects)  # ✅ added safely
            })

        data.append({
            "corporate_id": store.store_id,
            "corporate_name": store.name,
            "shops": shops_data
        })

    return Response({
        "success": True,
        "count": len(data),
        "data": data
    })
