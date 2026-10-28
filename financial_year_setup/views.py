import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


FINANCIAL_YEAR_API_URL = "https://centralmastermanagement.imcbs.com/api/financial-year/country-wise/"
MONTHS = ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER")


def _superuser_only(request):
    if not (request.user.is_authenticated and request.user.is_superuser):
        return HttpResponseForbidden("Permission denied")
    return None


def _api_request(method="GET", url=FINANCIAL_YEAR_API_URL, payload=None):
    body = None
    # Some WAF configurations block urllib's default `Python-urllib/...`
    # signature. Identify this as a normal JSON API client instead. The
    # permanent server-side fix is to whitelist this host or use the API's
    # official authentication mechanism if one is required.
    headers = {
        "Accept": "application/json",
        "User-Agent": "CentralLoginSystem/1.0 (+https://centralmastermanagement.imcbs.com/)",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(url, data=body, headers=headers, method=method), timeout=20) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            details = json.loads(raw)
        except json.JSONDecodeError:
            details = {"detail": raw or exc.reason}
        return exc.code, details
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(str(exc)) from exc


def _api_error_message(data):
    """Turn DRF detail and field-validation responses into a useful message."""
    if isinstance(data, dict):
        detail = data.get("detail") or data.get("message")
        if detail:
            return str(detail)
        errors = []
        for field, value in data.items():
            values = value if isinstance(value, list) else [value]
            errors.extend(f"{field}: {item}" for item in values)
        if errors:
            return "; ".join(errors)
    elif isinstance(data, list):
        return "; ".join(str(item) for item in data)
    return "The financial year service rejected the request."


def _form_payload(request):
    return {
        "country_name": request.POST.get("country_name", "").strip(),
        "country_code": request.POST.get("country_code", "").strip().upper(),
        "currency_code": request.POST.get("currency_code", "").strip().upper(),
        "fy_from_month": request.POST.get("fy_from_month", "").strip().upper(),
        "fy_to_month": request.POST.get("fy_to_month", "").strip().upper(),
        "remark": request.POST.get("remark", "").strip(),
    }


def _record_is_locked(record, request=None):
    """Return whether the central service has locked this country."""
    if request is not None:
        locked_ids = {str(item) for item in request.session.get("financial_year_locked_ids", [])}
        if str(record.get("id", "")) in locked_ids:
            return True
    lock_fields = ("is_locked", "is_lock", "locked", "lock", "lock_status")
    for field in lock_fields:
        value = record.get(field)
        if isinstance(value, str):
            if value.strip().lower() in {"1", "true", "yes", "locked", "on"}:
                return True
        elif value:
            return True
    return False


def _get_financial_year_record(financial_year_id):
    status_code, data = _api_request("GET", FINANCIAL_YEAR_API_URL)
    if status_code >= 400:
        return None, data
    records = data if isinstance(data, list) else data.get("results", data.get("data", []))
    if isinstance(records, dict):
        records = [records]
    record = next((item for item in records if int(item.get("id", -1)) == financial_year_id), None)
    return record, None


def _lock_financial_year(request, financial_year_id):
    denied = _superuser_only(request)
    if denied:
        return denied
    try:
        record, data = _get_financial_year_record(financial_year_id)
        if data is not None:
            messages.error(request, _api_error_message(data))
        elif record is None:
            messages.error(request, "The selected financial year was not found.")
        elif _record_is_locked(record, request):
            messages.error(request, "This country's financial year is already locked.")
        else:
            status_code, data = _api_request(
                "PATCH",
                f"{FINANCIAL_YEAR_API_URL}{financial_year_id}/",
                {"is_locked": True},
            )
            if status_code >= 400:
                messages.error(request, _api_error_message(data))
            else:
                locked_ids = set(request.session.get("financial_year_locked_ids", []))
                locked_ids.add(str(financial_year_id))
                request.session["financial_year_locked_ids"] = list(locked_ids)
                messages.success(request, "Financial year locked successfully. It cannot be unlocked.")
    except RuntimeError as exc:
        messages.error(request, f"Financial year service is unavailable: {exc}")
    return redirect("financial_year_setup:setup")


@login_required(login_url="login")
@require_http_methods(["GET"])
def financial_year_setup(request):
    denied = _superuser_only(request)
    if denied:
        return denied
    try:
        status_code, data = _api_request()
        records = data if isinstance(data, list) else data.get("results", data.get("data", []))
        if isinstance(records, dict):
            records = [records]
        records = [dict(record, is_locked=_record_is_locked(record, request)) for record in records]
        if status_code >= 400:
            messages.error(request, _api_error_message(data))
            records = []
    except RuntimeError as exc:
        messages.error(request, f"Financial year service is unavailable: {exc}")
        records = []
    return render(request, "financial_year_setup/setup_paginated.html", {"records": records, "months": MONTHS})


def _save_financial_year(request, method, url, success_message):
    denied = _superuser_only(request)
    if denied:
        return denied
    payload = _form_payload(request)
    if not payload["country_name"] or not payload["country_code"]:
        messages.error(request, "Country name and country code are required.")
        return redirect("financial_year_setup:setup")
    try:
        status_code, data = _api_request(method, url, payload)
        if status_code >= 400:
            messages.error(request, _api_error_message(data))
        else:
            messages.success(request, success_message)
    except RuntimeError as exc:
        messages.error(request, f"Financial year service is unavailable: {exc}")
    return redirect("financial_year_setup:setup")


@login_required(login_url="login")
@require_http_methods(["GET", "POST"])
def create_financial_year(request):
    denied = _superuser_only(request)
    if denied:
        return denied
    if request.method == "GET":
        return render(request, "financial_year_setup/create.html", {"months": MONTHS})
    return _save_financial_year(request, "POST", FINANCIAL_YEAR_API_URL, "Financial year created successfully.")


@login_required(login_url="login")
@require_http_methods(["POST"])
def lock_financial_year(request, financial_year_id):
    return _lock_financial_year(request, financial_year_id)


@login_required(login_url="login")
@require_http_methods(["GET", "POST"])
def update_financial_year(request, financial_year_id):
    denied = _superuser_only(request)
    if denied:
        return denied
    if request.method == "GET":
        try:
            # The remote API exposes GET on the collection endpoint only;
            # its detail endpoint accepts PATCH but rejects GET.
            status_code, data = _api_request("GET", FINANCIAL_YEAR_API_URL)
            if status_code >= 400:
                messages.error(request, _api_error_message(data))
                return redirect("financial_year_setup:setup")
            records = data if isinstance(data, list) else data.get("results", data.get("data", []))
            if isinstance(records, dict):
                records = [records]
            record = next((item for item in records if int(item.get("id", -1)) == financial_year_id), None)
            if record is None:
                messages.error(request, "The selected financial year was not found.")
                return redirect("financial_year_setup:setup")
            if _record_is_locked(record, request):
                messages.error(request, "This country's financial year is locked and cannot be edited.")
                return redirect("financial_year_setup:setup")
        except RuntimeError as exc:
            messages.error(request, f"Financial year service is unavailable: {exc}")
            return redirect("financial_year_setup:setup")
        return render(request, "financial_year_setup/edit.html", {"record": record, "months": MONTHS})
    try:
        record, data = _get_financial_year_record(financial_year_id)
        if data is not None:
            messages.error(request, _api_error_message(data))
            return redirect("financial_year_setup:setup")
        if record is None:
            messages.error(request, "The selected financial year was not found.")
            return redirect("financial_year_setup:setup")
        if _record_is_locked(record, request):
            messages.error(request, "This country's financial year is locked and cannot be edited.")
            return redirect("financial_year_setup:setup")
    except RuntimeError as exc:
        messages.error(request, f"Financial year service is unavailable: {exc}")
        return redirect("financial_year_setup:setup")
    return _save_financial_year(request, "PATCH", f"{FINANCIAL_YEAR_API_URL}{financial_year_id}/", "Financial year updated successfully.")

