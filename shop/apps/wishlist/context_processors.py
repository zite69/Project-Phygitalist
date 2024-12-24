def wishlists(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        return { "wishlists": request.user.wishlists.all() }

    return {}
