from rest_framework.pagination import PageNumberPagination

class PostPagination(PageNumberPagination):
    """
    PageNumberPagination for posts.

    - Default page size: 20
    - Client can override via ?page_size=
    - Hard cap to avoid abusive values
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CommentPagination(PageNumberPagination):
    """
    PageNumberPagination for comments under a post.

    - Default page size: 50
    - Client can override via ?page_size=
    - Hard cap to avoid abusive values
    """
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
