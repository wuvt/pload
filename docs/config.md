# Configuration Options

* `PLOAD_NAME` - Name of Pload instance
* `ELASTICSEARCH_HOSTS` - URL to Elasticsearch instances (used for search functionality)
* `TIME_SLOT_TZ` - Time zone to use for playlists
* `TRACKMAN_URL` - URL to Trackman instance (used for fetching DJ names)
* `TRACK_VALIDATE_CHECK_EXISTS` - Boolean indicating whether or not to check that track URLs return a 200
* `TRACK_URL_REWRITES` - List of tuples containing (regular expression, replacement) for rewriting actual track URLs
* `TRACK_URL_DISPLAY_REWRITES` - List of tuples containing (regular expression, replacement) for rewriting displayed track URLs
* `PROXY_FIX` - Boolean indicating whether or not to process X-Forwarded-For headers
* `PROXY_FIX_NUM_PROXIES` - Number of proxies used for X-Forwarded-For headers
