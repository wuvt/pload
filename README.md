# Pload

Pload is a web-based playlist loader for [johnny-six](https://github.com/wuvt/johnny-six).

It integrates a playlist builder with search using ElasticSearch. Users select
a time range for their show, what johnny-six queue they want to play from, and
what DJ they want johnny-six to log as. They then build or upload a playlist,
using tracks from the search or direct URLs as they see fit.

To retrieve tracks, Johnny-Six polls the API, which returns the next unplayed
track in the current show slot, marking it as played.
