from django.http import JsonResponse
from StoreShop.models import Shop  # import Shop model

def get_client_ids(request):
    client_ids = list(Shop.objects.values_list('client_id', flat=True))
    return JsonResponse({"client_ids": client_ids}, status=200)