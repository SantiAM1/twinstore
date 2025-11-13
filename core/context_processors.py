def canonical_url(request):
    """Genera la canonical URL limpia, sin parámetros GET"""
    scheme = "https" if request.is_secure() else "http"
    domain = request.get_host()
    path = request.path
    return {
        "canonical_url": f"{scheme}://{domain}{path}"
    }