from .models import Users


def get_user_branch_ids(request):
    """Return the branch IDs a logged-in custom (non-superuser) user may see.

    Returns:
        None  -> full access (superuser), filter nothing
        []    -> custom user with no assigned branches (sees nothing)
        [..]  -> custom user, restrict to these branch IDs
    """
    if request.user.is_authenticated and request.user.is_superuser:
        return None

    custom_user_id = request.session.get("custom_user_id")
    if not custom_user_id:
        return None

    user = Users.objects.filter(id=custom_user_id).first()
    if user is None:
        return []

    return list(user.branches.values_list("id", flat=True))