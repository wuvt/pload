# Pload

Pload is a web-based playlist loader for [johnny-six](https://github.com/wuvt/johnny-six).
It allows the user to select a time slot and upload a m3u file. The file is then
validated, parsed, and queued in the database. To retrieve tracks, there is an
API call that selects the first unplayed track for a time slot and returns it,
marking it as played.
