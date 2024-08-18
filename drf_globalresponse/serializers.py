from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from drf_globalresponse.app_settings import app_settings
from drf_globalresponse.fields import (
    HTTPCodeField,
    APIStatusField,
    MessageField,
    JSONResponseField,
)


class BaseGlobalResponseSerializer(Serializer):
    def __init__(self, *args, **kwargs):
        self.fields[app_settings.DATA_FIELD] = JSONResponseField(
            read_only=True,
            label=_("Data"),
            help_text=_("The data of the response."),
        )
        super().__init__(*args, **kwargs)


class GlobalResponseSerializer(BaseGlobalResponseSerializer):
    status = APIStatusField(
        label=_("Status"),
        help_text=_("The status of the response."),
        choices=["success", "client_error", "server_error"],
        default="success",
        read_only=True,
    )
    http_code = HTTPCodeField(
        label=_("HTTP Code"),
        help_text=_("The HTTP status code of the response."),
        read_only=True,
    )
    message = MessageField(
        label=_("Message"),
        help_text=_("The message of the response."),
        read_only=True,
    )
