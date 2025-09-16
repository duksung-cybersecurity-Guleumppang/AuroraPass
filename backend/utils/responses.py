from starlette.responses import JSONResponse
import json


class UTF8JSONResponse(JSONResponse):
    """
    JSONResponse with explicit UTF-8 charset and ensure_ascii disabled.
    Ensures Content-Type includes charset and Korean text is not escaped.
    """

    media_type = "application/json; charset=utf-8"

    def render(self, content) -> bytes:
        # Ensure ASCII off to keep Korean characters as-is
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")


