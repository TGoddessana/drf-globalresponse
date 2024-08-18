from rest_framework import status
from rest_framework.fields import IntegerField, ChoiceField, CharField, Field, JSONField

status_code_messages = {
    # 1XX
    status.HTTP_100_CONTINUE: "continue",
    status.HTTP_101_SWITCHING_PROTOCOLS: "switching_protocols",
    status.HTTP_102_PROCESSING: "processing",
    status.HTTP_103_EARLY_HINTS: "early_hints",
    # 2XX
    status.HTTP_200_OK: "ok",
    status.HTTP_201_CREATED: "created",
    status.HTTP_202_ACCEPTED: "accepted",
    status.HTTP_203_NON_AUTHORITATIVE_INFORMATION: "non_authoritative_information",
    status.HTTP_204_NO_CONTENT: "no_content",
    status.HTTP_205_RESET_CONTENT: "reset_content",
    status.HTTP_206_PARTIAL_CONTENT: "partial_content",
    status.HTTP_207_MULTI_STATUS: "multi_status",
    status.HTTP_208_ALREADY_REPORTED: "already_reported",
    status.HTTP_226_IM_USED: "im_used",
    # 3XX
    status.HTTP_300_MULTIPLE_CHOICES: "multiple_choices",
    status.HTTP_301_MOVED_PERMANENTLY: "moved_permanently",
    status.HTTP_302_FOUND: "found",
    status.HTTP_303_SEE_OTHER: "see_other",
    status.HTTP_304_NOT_MODIFIED: "not_modified",
    status.HTTP_305_USE_PROXY: "use_proxy",
    status.HTTP_306_RESERVED: "reserved",
    status.HTTP_307_TEMPORARY_REDIRECT: "temporary_redirect",
    status.HTTP_308_PERMANENT_REDIRECT: "permanent_redirect",
    # 4XX
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method not_allowed",
    status.HTTP_406_NOT_ACCEPTABLE: "not_acceptable",
    status.HTTP_408_REQUEST_TIMEOUT: "request_timeout",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_410_GONE: "gone",
    status.HTTP_411_LENGTH_REQUIRED: "length_required",
    status.HTTP_412_PRECONDITION_FAILED: "precondition_failed",
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "request_entity_too_large",
    status.HTTP_414_REQUEST_URI_TOO_LONG: "request_uri_too_long",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "unsupported_media_type",
    status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE: "requested_range_not_satisfiable",
    status.HTTP_417_EXPECTATION_FAILED: "expectation_failed",
    status.HTTP_418_IM_A_TEAPOT: "im_a_teapot",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "unprocessable_entity",
    status.HTTP_423_LOCKED: "locked",
    status.HTTP_424_FAILED_DEPENDENCY: "failed_dependency",
    status.HTTP_426_UPGRADE_REQUIRED: "upgrade_required",
    status.HTTP_428_PRECONDITION_REQUIRED: "precondition_required",
    status.HTTP_429_TOO_MANY_REQUESTS: "too_many_requests",
    status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE: "request_header_fields_too_large",
    status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS: "unavailable_for_legal_reasons",
    # 5XX
    status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_server_error",
    status.HTTP_501_NOT_IMPLEMENTED: "not_implemented",
    status.HTTP_502_BAD_GATEWAY: "bad_gateway",
    status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
    status.HTTP_504_GATEWAY_TIMEOUT: "gateway_timeout",
    status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED: "http_version_not_supported",
    status.HTTP_506_VARIANT_ALSO_NEGOTIATES: "variant_also_negotiates",
    status.HTTP_507_INSUFFICIENT_STORAGE: "insufficient_storage",
    status.HTTP_508_LOOP_DETECTED: "loop_detected",
    status.HTTP_510_NOT_EXTENDED: "not_extended",
    status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED: "network_authentication_required",
}


class RendererContextField(Field):
    """
    A field that can access the renderer context.
    """

    def get_attribute(self, instance):
        assert self.context.get("renderer_context"), (
            "Renderer context not set. You must set the `renderer_context` attribute "
            "on the view before instantiating the serializer."
        )
        return self.context.get("renderer_context")


class APIStatusField(RendererContextField, ChoiceField):
    def to_representation(self, value):
        http_code = value.get("response").status_code
        return (
            "success"
            if http_code < 400
            else "client_error"
            if http_code < 500
            else "server_error"
        )


class HTTPCodeField(RendererContextField, IntegerField):
    def to_representation(self, value):
        return value.get("response").status_code


class MessageField(RendererContextField, CharField):
    def to_representation(self, value):
        """
        from a response body, create a summary message about the overall API response.

        if no error occurred basically, return a message based on the HTTP status code.
        but if there are `message` field in the response body, return additional message.
        for example, if the HTTP status code is 200 and the response body is like
         `{"message": "some operation is successful"}`, return "ok(some operation is successful)".

        if an error occurred, return a message based on the error message.
        for example, if the HTTP status code is 403 and the error message is "permission denied",
        return "forbidden(permission denied)".

        we also handle the case where the error message is a list.
        for example, if the multiple fields are invalid,
        return "bad_request(field1: error1, field2: error2)".

        Note that the current implementaion is strongly coupled to drf's default error handler.
        if you use a custom error handler, you may need to modify this method.
        """
        http_code = value.get("response").status_code
        prefix = status_code_messages.get(http_code, "unknown_error")

        if not value["response"].exception:
            message = value["response"].data.get("message")

            # if "message" in response body, build a message based on the HTTP status code and the message.
            if message:
                return prefix + f"({message})"
            return prefix

        if value["response"].exception:
            error = value["response"].data
            if isinstance(error, list):
                error_summary = f"({', '.join(error)})"
            else:
                field_and_message = []
                for field, error_details in error.items():
                    if isinstance(error_details, list):
                        for errordetail in error_details:
                            # if `.` is the last character, remove it
                            if errordetail[-1] == ".":
                                errordetail = errordetail[:-1]
                            field_and_message.append(f"{field}: {errordetail}")
                    else:
                        field_and_message.append(f"{field}: {error_details}")

                error_summary = ", ".join(field_and_message)
                error_summary = f"({error_summary})"
            return prefix + error_summary


class JSONResponseField(RendererContextField, JSONField):
    def to_representation(self, value):
        return value.get("response").data
