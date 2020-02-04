from pydantic import BaseModel, Field


class ErrorSchema(BaseModel):
    message: str = Field(
        ..., description="Human-readable error message.", example="Something went wrong."
    )


class InternalErrorSchema(ErrorSchema):
    exception_id: str = Field(
        ...,
        description="Unique identifier for the error that occurred. Provide this to system "
        "administrators if you are reporting an error.",
        example="dd4c4fa3-8d22-4768-8b0d-0923140d9f8a",
    )


class SearchQuery(BaseModel):
    # TODO stub
    pass


class SearchResponse(BaseModel):
    # TODO stub
    pass
