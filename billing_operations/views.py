import json
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.utils import timezone
from django.db.models import OuterRef, Subquery
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from login_with_token.views import get_user_from_token
from MobileApp.models import MobileControl, MobileBillingHistory


def _billing_history_data(record):
    return {
        'id': record.id,
        'bill_status': record.bill_status,
        'payment_status': record.payment_status,
        'invoice_number': record.invoice_number,
        'invoice_amount': str(record.invoice_amount) if record.invoice_amount else None,
        'ref_no': record.ref_no,
        'ref_no_saved_at': record.ref_no_saved_at.isoformat() if record.ref_no_saved_at else None,
        'remark': record.remark,
        'extended_days': record.extended_days,
        'extended_login_limit': record.extended_login_limit,
        'old_expiry_date': record.old_expiry_date.isoformat() if record.old_expiry_date else None,
        'new_expiry_date': record.new_expiry_date.isoformat() if record.new_expiry_date else None,
        'old_login_limit': record.old_login_limit,
        'new_login_limit': record.new_login_limit,
        'package': record.package.package_name if record.package else None,
        'custom_package': record.custom_package.package_name if record.custom_package else None,
        'added_by': record.added_by,
        'created_at': record.created_at.isoformat() if record.created_at else None,
    }


def _unbilled_license_data(control, now):
    remaining_days = None
    is_expired = False
    if control.expiry_date:
        delta = control.expiry_date - now
        remaining_days = delta.days
        is_expired = delta.total_seconds() <= 0

    return {
        'id': control.id,
        'customer_name': control.customer_name,
        'client_id': control.client_id,
        'license_key': control.license_key,
        'project': control.project.project_name if control.project else None,
        'app_type': control.project.app_type if control.project else None,
        'package': control.package.package_name if control.package else None,
        'custom_package': control.active_custom_package.package_name if control.active_custom_package else None,
        'branch': control.shop.branch.name if control.shop and control.shop.branch else None,
        'store': control.store.name if control.store else None,
        'shop': control.shop.name if control.shop else None,
        'status': control.status,
        'bill_status': control.bill_status,
        'login_limit': control.login_limit,
        'registered_devices': control.active_devices.count(),
        'expiry_date': control.expiry_date.isoformat() if control.expiry_date else None,
        'remaining_days': remaining_days,
        'is_expired': is_expired,
        'licence_type': control.licence_type,
        'created_date': control.created_date.isoformat() if control.created_date else None,
        'updated_date': control.updated_date.isoformat() if control.updated_date else None,
        'latest_payment_status': getattr(control, 'latest_payment_status', None),
        'unbilled_history': [
            _billing_history_data(h)
            for h in control.billing_history.filter(bill_status=False).order_by('-created_at')
        ],
    }


@csrf_exempt
@require_http_methods(["GET"])
def api_unbilled_licenses(request):
    """GET /api/billing-operations/unbilled/
    Returns all unbilled licenses (MobileControl.bill_status=False) with full details.
    No authentication required."""
    now = timezone.now()

    latest_payment_sub = MobileBillingHistory.objects.filter(
        control=OuterRef('pk')
    ).order_by('-created_at').values('payment_status')[:1]

    controls = (
        MobileControl.objects
        .filter(bill_status=False)
        .annotate(latest_payment_status=Subquery(latest_payment_sub))
        .select_related('project', 'package', 'active_custom_package', 'shop__branch', 'store')
        .order_by('-updated_date')
    )

    unbilled = [_unbilled_license_data(c, now) for c in controls]

    return JsonResponse({
        'success': True,
        'count': len(unbilled),
        'unbilled': unbilled,
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_bill_license(request):
    """POST /api/billing-operations/bill/
    Marks an unbilled billing record (MobileBillingHistory) as billed.
    Body (JSON):
      - billing_id                (required)
      - invoice_number            (required)
      - invoice_amount            (required)
      - payment_status            (optional: Paid / Partially Paid / Not Paid / Not Applicable)
      - ref_no                    (optional, required if payment_status is Paid/Partially Paid)
      - remark                    (optional)
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    billing_id = data.get('billing_id')

    invoice_number = (data.get('invoice_number') or '').strip()
    invoice_amount = data.get('invoice_amount')
    payment_status = (data.get('payment_status') or 'Not Paid').strip()
    ref_no = (data.get('ref_no') or '').strip()
    remark = (data.get('remark') or '').strip()

    if not billing_id:
        return JsonResponse({'success': False, 'error': 'billing_id is required'}, status=400)

    if not invoice_number:
        return JsonResponse({'success': False, 'error': 'invoice_number is required'}, status=400)

    try:
        invoice_amount = Decimal(invoice_amount)
    except (InvalidOperation, TypeError):
        return JsonResponse({'success': False, 'error': 'Valid invoice_amount is required'}, status=400)

    valid_statuses = dict(MobileBillingHistory.PAYMENT_STATUS_CHOICES)
    if payment_status not in valid_statuses:
        return JsonResponse({'success': False, 'error': 'Invalid payment_status'}, status=400)

    if payment_status in ('Paid', 'Partially Paid') and not ref_no:
        return JsonResponse({'success': False, 'error': 'ref_no is required for paid statuses'}, status=400)

    try:
        record = MobileBillingHistory.objects.select_related('control', 'control__shop__branch').get(pk=billing_id)
    except MobileBillingHistory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Billing record not found'}, status=404)
    targets = [record]

    billed_records = []
    for record in targets:
        if record.bill_status:
            continue

        record.bill_status = True
        record.invoice_number = invoice_number
        record.invoice_amount = invoice_amount
        record.payment_status = payment_status
        record.remark = remark or record.remark
        if ref_no:
            record.ref_no = ref_no
            record.ref_no_saved_at = timezone.now()
        record.save()

        control = record.control
        control.bill_status = not control.billing_history.filter(bill_status=False).exists()
        control.save(update_fields=['bill_status', 'updated_date'])

        billed_records.append(_billing_history_data(record))

    return JsonResponse({
        'success': True,
        'message': f'{len(billed_records)} record(s) marked as billed',
        'count': len(billed_records),
        'billed': billed_records,
    })