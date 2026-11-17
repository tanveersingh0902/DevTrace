class ApplicationError(Exception):
    """Safe, explicitly selected public error; never attach database exceptions."""

    def __init__(
        self, status_code: int, code: str, detail: str, *, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.headers = headers
