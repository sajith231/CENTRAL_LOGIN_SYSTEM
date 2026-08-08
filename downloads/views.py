from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .r2 import get_r2
import logging
import os

from StoreShop.models import Shop

logger = logging.getLogger(__name__)

BUCKET = os.getenv("CLOUDFLARE_R2_BUCKET")


def _safe_filename(filename):
    """Strip path components and control chars from a client-supplied filename."""
    name = os.path.basename((filename or "").strip()).replace("\x00", "").strip()
    if not name or name in (".", ".."):
        return None
    return name[:255]


def upload_presign(request):
    """Return a presigned PUT URL so the browser uploads directly to R2.

    Keeps large files (e.g. APKs) out of the gunicorn/nginx request path,
    which avoids 502s caused by worker timeouts or overload.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    folder = (request.POST.get("folder") or "").strip()
    filename = _safe_filename(request.POST.get("filename"))
    content_type = request.POST.get("content_type") or "application/octet-stream"

    if not folder or "/" in folder or ".." in folder:
        return JsonResponse({"error": "Folder name is required"}, status=400)
    if not filename:
        return JsonResponse({"error": "Invalid file name"}, status=400)

    key = f"{folder}/{filename}"
    r2 = get_r2()

    try:
        presigned_url = r2.generate_presigned_url(
            "put_object",
            Params={"Bucket": BUCKET, "Key": key, "ContentType": content_type},
            ExpiresIn=3600,
        )
    except Exception as e:
        logger.exception("Error generating presigned URL for %s", key)
        return JsonResponse({"error": f"Could not prepare upload: {e}"}, status=500)

    return JsonResponse({
        "success": True,
        "presigned_url": presigned_url,
        "key": key,
        "filename": filename,
        "content_type": content_type,
    })


def qr_verify(request):
    """Public page opened when a licence QR code is scanned.
    The QR encodes a site URL: /downloads/verify/?client_id=...&key=...
    Shows the client id with a copy option."""
    client_id = request.GET.get("client_id", "").strip()
    licence_key = request.GET.get("key", "").strip()

    company = None
    if client_id:
        shop = Shop.objects.filter(client_id=client_id).select_related("store", "branch").first()
        if shop:
            company = {
                "name": shop.name,
                "place": shop.place,
                "email": shop.email,
                "contact_no": shop.contact_no,
                "country": shop.country,
                "branch": shop.branch.name if shop.branch else None,
                "corporate": shop.store.name if shop.store else None,
            }

    return render(request, "qr_verify.html", {
        "client_id": client_id,
        "licence_key": licence_key,
        "company": company,
    })

# ---------- UPLOAD PAGE ----------
def upload_page(request):
    r2 = get_r2()

    if request.method == "POST":
        folder = (request.POST.get("folder") or "").strip()
        files = request.FILES.getlist("files")

        if not folder:
            return JsonResponse({"error": "Folder name is required"}, status=400)

        if not files:
            return JsonResponse({"error": "No files selected"}, status=400)

        uploaded_count = 0
        failed = []
        for f in files:
            try:
                key = f"{folder}/{f.name}"
                r2.upload_fileobj(f, BUCKET, key)
                uploaded_count += 1
            except Exception as e:
                logger.exception("Error uploading %s to %s", f.name, folder)
                failed.append({"name": f.name, "error": str(e)})

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if uploaded_count == 0 and failed:
                return JsonResponse({
                    "success": False,
                    "error": f"Upload failed for {len(failed)} file(s): {failed[0]['error']}",
                    "failed": failed,
                }, status=500)

            return JsonResponse({
                "success": True,
                "message": f"{uploaded_count} file(s) uploaded successfully",
                "count": uploaded_count,
                "failed": failed,
            })
        
        return redirect("downloads:upload")

    # list folders with file details
    objects = r2.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    folders_data = {}
    
    for obj in objects:
        if "/" in obj["Key"]:
            folder_name = obj["Key"].split("/")[0]
            file_name = obj["Key"].split("/", 1)[1]  # Get filename after folder
            
            if folder_name not in folders_data:
                folders_data[folder_name] = {
                    "name": folder_name,
                    "file_count": 0,
                    "total_size": 0,
                    "files": []
                }
            folders_data[folder_name]["file_count"] += 1
            folders_data[folder_name]["total_size"] += obj.get("Size", 0)
            folders_data[folder_name]["files"].append({
                "name": file_name,
                "size": obj.get("Size", 0)
            })

    folders = sorted(folders_data.values(), key=lambda x: x["name"])

    return render(request, "upload.html", {"folders": folders})


def delete_folder(request, name):
    if request.method == "POST":
        r2 = get_r2()
        objs = r2.list_objects_v2(Bucket=BUCKET, Prefix=f"{name}/").get("Contents", [])

        deleted_count = 0
        for obj in objs:
            try:
                r2.delete_object(Bucket=BUCKET, Key=obj["Key"])
                deleted_count += 1
            except Exception as e:
                logger.exception("Error deleting %s", obj["Key"])

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": True,
                "message": f"Folder '{name}' deleted successfully",
                "count": deleted_count
            })

    return redirect("downloads:upload")


def delete_file(request, folder, filename):
    if request.method == "POST":
        r2 = get_r2()
        key = f"{folder}/{filename}"
        try:
            r2.delete_object(Bucket=BUCKET, Key=key)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "message": f"File '{filename}' deleted successfully"
                })
        except Exception as e:
            logger.exception("Error deleting file %s", key)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "message": str(e)}, status=500)

    return redirect("downloads:upload")


# ---------- DOWNLOAD PAGE ----------
def download_page(request):
    r2 = get_r2()
    q = request.GET.get("q", "").lower()

    objects = r2.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    folders = {}

    for obj in objects:
        parts = obj["Key"].split("/")
        if len(parts) > 1:
            folder = parts[0]
            file = parts[1]
            if q and q not in folder.lower() and q not in file.lower():
                continue
            
            if folder not in folders:
                folders[folder] = []
            
            folders[folder].append({
                "name": file,
                "size": obj.get("Size", 0),
                "last_modified": obj.get("LastModified")
            })

    # Sort folders and files
    folders = dict(sorted(folders.items()))
    for folder in folders:
        folders[folder] = sorted(folders[folder], key=lambda x: x["name"])

    # Calculate total files
    total_files = sum(len(files) for files in folders.values())

    return render(request, "download.html", {"folders": folders, "q": q, "total_files": total_files})


def download_file(request, folder, filename):
    r2 = get_r2()
    key = f"{folder}/{filename}"
    
    try:
        obj = r2.get_object(Bucket=BUCKET, Key=key)
        response = HttpResponse(obj['Body'].read(), content_type=obj.get('ContentType', 'application/octet-stream'))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        return HttpResponse(f"Error downloading file: {e}", status=404)