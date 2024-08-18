from rest_framework.renderers import JSONRenderer

from drf_globalresponse.app_settings import app_settings


class GlobalResponseJSONRenderer(JSONRenderer):
    serializer_class = app_settings.GLOBAL_SERIALIZER

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_data = self.serializer_class(
            data,
            context={"renderer_context": renderer_context},
        ).data

        return super().render(
            response_data,
            accepted_media_type,
            renderer_context,
        )
