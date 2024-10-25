I was looking for an updated danbooru tag list but I couldn't find a recent one that was in the correct format, so I made my own.

Based on this original script: https://gist.github.com/bem13/596ec5f341aaaefbabcbf1468d7852d5

requires the requests library (`pip install requests`)

Main Changes:
- Allows setting minimum post threshold
- Allows '-' format (found to be better for prompt following)
- Saves tag categories (used by SwarmUI and tag-complete)
- Uses the UI's expected formatting
- Slightly faster rate limit
- Ability to exclude tag categories
- The option to include aliases (UI support varies)

About the uploaded list:

I uploaded my own list generated using the script for convenience. The minimum threshold was 50, '-' formatting and aliases were enabled. I may or may not update this list when I feel enough time has passed, probably not until a model with newer data is released.

The format is as follows:

|tag|category|post count|aliases(if enabled)|
|---|--------|----------|-----------------------------------------|
