import logging

from fastapi import Request

# All routes are private by default
#   if a route is not here, the tokens will be validated before processing
#   the request
PUBLIC_ROUTES = [
    '/auth',
    '/auth/login',
    '/auth/logout',
    '/properties'
]


# Add trailing slashes to all routes
# for r in PUBLIC_ROUTES:
#     if r[-1] == '/':
#         raise Exception('Routes cannont be defined with trailing slashes')


def is_public_route(request: Request):
    """
    A helper function that determines if a route is public or not.
    if a request has a trailing slash, it is removed before checking
    """
    path = request.url.path
    if path[-1] == '/':
        path = path[:-1]
    public = path in PUBLIC_ROUTES
    if not public:
        logging.warning(f"Route {path} is not public")
    return public
