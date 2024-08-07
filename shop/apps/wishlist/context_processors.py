def wishlists(request):
    if request.user and request.user.is_authenticated:
        return { "wishlists": request.user.wishlists.all() }

    return {}
