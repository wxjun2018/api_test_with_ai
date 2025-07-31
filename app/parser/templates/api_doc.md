# API Documentation

Generated at {{ now() }}

{% for api in apis %}
## {{ api.method }} {{ api.path }}

{{ api.description }}

### Request

{% if api.request.headers %}
#### Headers

| Name | Type | Required | Example |
|------|------|----------|---------|
{% for name, header in api.request.headers.items() %}
| {{ name }} | {{ header.type }} | {{ header.required }} | {{ header.example }} |
{% endfor %}
{% endif %}

{% if api.request.query_params and api.request.query_params.properties %}
#### Query Parameters

| Name | Type | Example |
|------|------|---------|
{% for name, param in api.request.query_params.properties.items() %}
| {{ name }} | {{ param.type }} | {{ param.example }} |
{% endfor %}
{% endif %}

{% if api.request.body %}
#### Request Body

```json
{{ api.request.body | tojson(indent=2) }}
```
{% endif %}

### Response

Status Code: {{ api.response.status_code }}

{% if api.response.headers %}
#### Headers

| Name | Type | Required | Example |
|------|------|----------|---------|
{% for name, header in api.response.headers.items() %}
| {{ name }} | {{ header.type }} | {{ header.required }} | {{ header.example }} |
{% endfor %}
{% endif %}

{% if api.response.body %}
#### Response Body

```json
{{ api.response.body | tojson(indent=2) }}
```
{% endif %}

{% endfor %} 