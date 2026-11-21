# Your own bar

The app ships with an example bar (`inventory.example.json`). To use your own:

1. Photograph your bottles, mixers and fridge door: labels facing the camera, a few bottles per photo.
2. Give the photos to your own AI tool with the prompt below.
3. Check the list it gives back, save it as `inventory.json`, and load it with **Your bar → Load my bar**.

`inventory.json` is in `.gitignore`, so it never reaches this repository. The app reads it in your browser only.

## Prompt

> These photos show the drinks in my home bar. List every spirit, liqueur, vermouth, bitters, syrup, mixer and fresh ingredient you can identify, as JSON in this shape: `{"bar": "My bar", "updated": "YYYY-MM-DD", "have": ["bourbon", "sweet vermouth", ...]}`. Use these names where they fit: the keys of the example file, all lower case. If you can't read a label, add it to a separate `"unsure"` list with a short description instead of guessing.
