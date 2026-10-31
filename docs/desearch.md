# Desearch web search

Get an API key at https://console.desearch.ai and set `DESEARCH_API_KEY` in the
process environment. In `~/.metagpt/config2.yaml`, select:

```yaml
search:
  api_type: desearch
```

The provider also accepts `search.api_key`. An explicit key takes precedence over
the environment variable. Keep keys out of source control.

Desearch uses `GET https://api.desearch.ai/web` with Bearer authentication and
returns titles, links, and snippets. `max_results` limits the returned results
locally because this endpoint returns a page of up to 20 results and has no
server-side count parameter. No extra dependencies are required.

API documentation: https://desearch.ai/docs
