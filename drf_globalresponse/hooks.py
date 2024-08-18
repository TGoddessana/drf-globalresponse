import copy

from drf_spectacular.plumbing import (
    build_basic_type,
)
from rest_framework import serializers

from drf_globalresponse.app_settings import app_settings


def get_schema_from_serializer(serializer):
    """
    Generate drf-spectacular schema from a serializer.
    """
    properties = {}

    field_type_mapping = {
        serializers.ChoiceField: lambda openapi_field: {
            "type": "string",
            "enum": list(field.choices.keys()),
        },
        serializers.IntegerField: lambda openapi_field: {
            "type": "integer",
        },
        serializers.CharField: lambda openapi_field: {
            "type": "string",
        },
        serializers.JSONField: lambda openapi_field: {
            "type": "object",
        },
        serializers.BooleanField: lambda openapi_field: {
            "type": "boolean",
        },
        serializers.FloatField: lambda openapi_field: {
            "type": "number",
        },
        serializers.DateField: lambda openapi_field: {
            "type": "string",
            "format": "date",
        },
        serializers.DateTimeField: lambda openapi_field: {
            "type": "string",
            "format": "date-time",
        },
        serializers.EmailField: lambda openapi_field: {
            "type": "string",
            "format": "email",
        },
        serializers.URLField: lambda openapi_field: {
            "type": "string",
            "format": "uri",
        },
        serializers.SerializerMethodField: lambda openapi_field: build_basic_type(
            field
        ),
    }

    for field_name, field in serializer.fields.items():
        field_schema = None
        for field_type, schema_func in field_type_mapping.items():
            if isinstance(field, field_type):
                field_schema = schema_func(field)
                break
        if field_schema is None:
            field_schema = build_basic_type(field)
        if field.read_only:
            field_schema["readOnly"] = True
        if field.label:
            field_schema["title"] = field.label
        if field.help_text:
            field_schema["description"] = field.help_text
        properties[field_name] = field_schema

    return {
        "type": "object",
        "properties": properties,
    }


def globalresponse_postprocessing_hook(result, generator, request, public):
    """
    Postprocessing hook to generate a global response schema for all responses.
    """
    serializer = app_settings.GLOBAL_SERIALIZER()
    base_generated_schema = get_schema_from_serializer(serializer)
    result.setdefault("components", {}).setdefault("schemas", {})

    for methods in result["paths"].values():
        for operation in methods.values():
            responses = operation.get("responses", {})
            for response in responses.values():
                content = response.get("content", {}).get("application/json", {})
                schema = content.get("schema", {})
                original_schema_name = schema.get("$ref", "").split("/")[-1]
                schema_name = f"{original_schema_name}GlobalResponse"

                generated_schema = copy.deepcopy(base_generated_schema)
                generated_schema["properties"][app_settings.DATA_FIELD] = schema
                result["components"]["schemas"][schema_name] = generated_schema

                content["schema"] = {"$ref": f"#/components/schemas/{schema_name}"}
    return result
