from typing import Any, Dict, List

from fastapi import Query, Request, Response
from sqlalchemy import orm
from typing_extensions import TypedDict


class PaginatedResponse(TypedDict):
    count: int
    results: List[Dict[str, Any]]


class Pagination:
    """
    This class is responsible for generating paged responses from sqlalchemy queries.
    """

    DEFAULT_OFFSET = 0
    DEFAULT_LIMIT = 25

    def __init__(
        self,
        request: Request,
        response: Response,
        offset: int = Query(default=DEFAULT_OFFSET, ge=0),
        limit: int = Query(default=DEFAULT_LIMIT, ge=1),
    ):
        self._request = request
        self._response = response
        self.offset = offset
        self.limit = limit

    def paginate(self, query: orm.Query, count: int) -> orm.Query:
        return query.limit(self.limit).offset(self.offset)

    def headers(self, query: orm.Query, count: int) -> Dict[str, str]:
        """Generate pagination link headers.

        https://datatracker.ietf.org/doc/html/rfc5988
        """

        def url(name: str, offset: int) -> str:
            return (
                f"<{self._request.url.include_query_params(limit=self.limit, offset=offset)}>; "
                f'rel="{name}"'
            )

        links = [
            url("first", 0),
        ]

        last = ((count - 1) // self.limit) * self.limit
        previous = self.offset - self.limit
        next = self.offset + self.limit
        if count:
            links.append(url("last", last))
        if previous >= 0:
            links.append(url("previous", previous))
        if next < count:
            links.append(url("next", next))

        return {
            "Links": ", ".join(links),
            "Resource-Count": str(count),
        }

    def response(self, query: orm.Query, processor=lambda x: x) -> PaginatedResponse:
        """Serialize a paged response from a query.

        Optionally, pass in a function to perform extra processing on each item
        prior to serialization.
        """
        count = query.count()
        self._response.headers.update(self.headers(query, count))
        return {
            "results": [processor(x) for x in self.paginate(query, count)],
            "count": count,
        }
