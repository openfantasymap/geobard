"""geobard — turn GeoJSON into prose.

Three modes:

  - narrate_window_view(geojson, system, detail_level)
  - narrate_with_prompt(geojson, prompt, system)
  - image_prompt(geojson, image_system, detail_level)

Any OpenAI-compatible chat-completions endpoint; defaults to OpenRouter.
"""
