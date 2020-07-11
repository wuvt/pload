function PlaylistEditor(baseUrl) {
    this.baseUrl = baseUrl;
    this.displayRewrites = [];
}

PlaylistEditor.prototype.init = function() {
    this.initPlaylist();
    this.initImport();
};

PlaylistEditor.prototype.initPlaylist = function() {
    this.playlist = [];
    this.draggedPlaylistId = null;
    this.draggedPlaylistDropId = null;

    $('#playlist').on('dragenter', {'instance': this}, function(ev) {
        var inst = ev.data.instance;
        var target = ev.target;

        if(target.tagName == "A") {
            target = target.parentElement;
        }
        if(target.tagName == "TD") {
            target = target.parentElement;
        }
        if(target.tagName == "TR") {
            $(target).addClass('drag-over');
            inst.draggedPlaylistDropId = $(target).attr('data-playlist-id');
        }
    });
    $('#playlist').on('dragleave', {'instance': this}, function(ev) {
        var inst = ev.data.instance;
        var target = ev.target;

        if(target.tagName == "A") {
            target = target.parentElement;
        }
        if(target.tagName == "TD") {
            target = target.parentElement;
        }
        if(target.tagName == "TR") {
            if($(target).attr('data-playlist-id') != inst.draggedPlaylistDropId) {
                $(target).removeClass('drag-over');
            }
        }
    });
    $('#playlist').on('dragover', function(ev) {
        ev.preventDefault();
    });
    $('#playlist').on('drop', {'instance': this}, this.dropPlaylistItem);

    $("button#add_track").on('click', {'instance': this},
                             this.addTrack);
    $("form#playlist_form").on('submit', {'instance': this},
                               this.addTrack);
    $("button#search_tracks_btn").on('click', {'instance': this},
                                     this.searchForTracks);
    $("form#playlist_search_form").on('submit', {'instance': this},
                                      this.searchForTracks);
};

PlaylistEditor.prototype.dropPlaylistItem = function(ev) {
    var inst = ev.data.instance;
    ev.preventDefault();

    var target = ev.target;
    if(target.tagName == "A") {
        target = target.parentElement;
    }
    if(target.tagName == "TD") {
        target = target.parentElement;
    }
    if(target.tagName == "TR") {
        var draggedId = inst.draggedPlaylistId;
        var draggedItem = inst.playlist[inst.draggedPlaylistId];
        var targetId = $(target).attr("data-playlist-id");

        // remove existing entry for dragged item in playlist
        inst.playlist.splice(inst.draggedPlaylistId, 1);

        // add new entry for dragged item in playlist
        // since the IDs will have now changed, we need to compensate based
        // on where the dragged item was in the playlist
        if(draggedId > targetId) {
            var newId = parseInt(targetId) + 1;
            inst.playlist.splice(newId, 0, draggedItem);
        } else {
            inst.playlist.splice(targetId, 0, draggedItem);
        }

        // reset dragged item variables
        inst.draggedPlaylistId = null;
        inst.draggedPlaylistDropId = null;

        // redraw playlist and save
        inst.updatePlaylist();
    }
};

PlaylistEditor.prototype.loadPlaylist = function(existingTracks) {
    for (var i = 0; i < existingTracks.length; i++) {
        this.playlist.push({
            'url': existingTracks[i]['url'],
        });
    }

    this.updatePlaylist();
};

PlaylistEditor.prototype.updatePlaylist = function() {
    $("table#playlist tbody tr").remove();
    for (var i = 0; i < this.playlist.length; i++) {
        var result = this.playlist[i];
        $("table#playlist tbody").append(this.renderTrackRow({
            'id': i,
            'url': result['url'],
        }, 'playlist'));
    }
};

PlaylistEditor.prototype.renderTrackRow = function(track, context) {
    var row = $('<tr>');
    var cols = [];

    if(context == 'playlist') {
        cols.push('url');

        row.addClass('playlist-row');
        row.attr('data-playlist-id', track['id']);

        row.prop('draggable', true);
        row.on('dragstart', {'instance': this}, function(ev) {
            ev.data.instance.draggedPlaylistId = track['id'];
        });
        row.on('dragend', {'instance': this}, function(ev) {
            ev.data.instance.draggedPlaylistDropId = null;
        });
    } else if(context == 'search_results') {
        if(typeof track['title'] == 'undefined') {
            track['title'] = track['song'];
        }

        cols.push('artist', 'title', 'album', 'label', 'url');

        row.attr('data-url', track['url']);
    }

    // main text entries

    for(let c in cols) {
        var td = $('<td>');

        var colName = cols[c];
        td.addClass(colName);

        if(colName == 'url') {
            link = $('<a>');
            link.attr('href', this.processDisplayUrl(track[colName]));
            link.attr('rel', 'noopener');
            link.attr('target', '_blank');
            link.text(decodeURI(this.processDisplayUrl(track[colName])));
            td.append(link);
        } else {
            td.text(track[colName]);
        };

        row.append(td);
    }

    // buttons

    var td = $('<td>');
    td.addClass('text-right');
    var group = $('<div>');
    group.addClass('btn-group');
    td.append(group);
    row.append(td);

    if(context == 'playlist') {
        group.addClass('playlist-actions');

        /*var editBtn = $("<button class='btn btn-secondary btn-sm playlist-edit' title='Edit this track'><span class='oi oi-pencil'></span></button>");
        editBtn.on('click', {'instance': this, 'context': 'playlist'},
                   this.inlineEditTrack);
        group.append(editBtn);*/

        var deleteBtn = $("<button class='btn btn-danger btn-sm playlist-delete' type='button' title='Delete this track from playlist'><span class='oi oi-trash'></span></button>");
        deleteBtn.on('click', {'instance': this}, function(ev) {
            ev.data.instance.removeFromPlaylist(row);
        });
        group.append(deleteBtn);
    } else if(context == 'search_results') {
        group.addClass('playlist-actions');

        var addBtn = $("<button class='btn btn-primary btn-sm search-add' type='button' title='Add this track to the playlist'><span class='oi oi-plus'></span></button>");
        addBtn.on('click', {'instance': this}, function(ev) {
            var inst = ev.data.instance;
            inst.playlist.push(track);
            inst.updatePlaylist();
        });
        group.append(addBtn);
    }

    return row;
};

PlaylistEditor.prototype.addTrack = function(ev) {
    var inst = ev.data.instance;

    // don't submit form
    ev.preventDefault();

    var newTrack = {
        "url": $('input#url').val(),
    };

    $.ajax({
        url: inst.baseUrl + "/api/validate_track",
        dataType: "json",
        data: newTrack,
        success: function(data) {
            if(data['result'] == true) {
                $('input#url').val('');
                newTrack['url'] = data['url'];

                inst.playlist.push(newTrack);
                inst.updatePlaylist();
            } else {
                console.log("Track failed to validate: " + JSON.stringify(newTrack));
            }
        },
    });
};

PlaylistEditor.prototype.removeFromPlaylist = function(element) {
    id = $(element).attr('data-playlist-id');
    this.playlist.splice(id, 1);
    this.updatePlaylist();
};

PlaylistEditor.prototype.listTracks = function() {
    var tracks = [];
    for(let t in playlistEditor.playlist) {
        tracks.push(playlistEditor.playlist[t]['url']);
    }
    return tracks;
};

PlaylistEditor.prototype.searchForTracks = function(ev) {
    var inst = ev.data.instance;

    // don't submit form
    ev.preventDefault();

    $.ajax({
        method: "GET",
        url: inst.baseUrl + "/api/search",
        dataType: "json",
        data: {
            "q": $('#playlist_search_form input#q').val(),
        },
        success: function(data) {
            $("table#search_results tbody tr").remove();
            for (var i = 0; i < data['hits'].length; i++) {
                var result = data['hits'][i];
                $("table#search_results tbody").append(inst.renderTrackRow(
                    result['_source'], 'search_results'));
            }
        },
    });
};

PlaylistEditor.prototype.processDisplayUrl = function(url) {
    for(let i = 0; i < this.displayRewrites.length; i++) {
        let re = new RegExp(this.displayRewrites[i][0]);
        url = url.replace(re, this.displayRewrites[i][1]);
    }

    return url;
};

PlaylistEditor.prototype.initImport = function() {
    $("button#import_m3u_submit_btn").on('click', {'instance': this}, function(ev) {
        var inst = ev.data.instance;

        var uploadControl = document.getElementById('import_m3u_input');
        if(uploadControl.files.length != 1) {
            alert("Upload only one file a time.");
            return;
        }

        var playlistFile = uploadControl.files[0];
        if(playlistFile.type != "audio/x-mpegurl" && !playlistFile.type.startsWith("text/")) {
            alert("The playlist file does not appear to be the correct file type.");
            return;
        }

        var reader = new FileReader();

        // Heads up, this is a little bit complex as it uses some modern ES6+
        // magic to work!
        //
        // We wrap the whole onload event handler in an anonymous function to
        // past in an instance of PlaylistEditor. Then, the event handler
        // itself uses async/await to handle tracks in the playlist serially.
        // Basically, what happens is calling processPlaylist (an async
        // function) runs processPlaylist without blocking the event handler.
        //
        // Inside processPlaylist, we loop through the list like normal, but
        // instead of passing a callback to $.ajax, we use await with it. This
        // pauses processing until that call returns and we get a result back.
        //
        // We check the value of the result; if the track is valid, just add
        // it to the playlist. If not, display an alert to the user and abort.
        // It's on them to manually remove tracks if something went horribly
        // wrong with the import.
        reader.onload = (function(inst) {
            return function(ev) {
                async function processPlaylist(playlist) {
                    for(let i = 0; i < playlist.length; i++) {
                        // skip empty lines
                        if(playlist[i].length <= 0) {
                            continue;
                        }

                        let newTrack = {
                            "url": playlist[i],
                        };

                        const result = await $.ajax({
                            url: inst.baseUrl + "/api/validate_track",
                            dataType: "json",
                            data: newTrack,
                        });

                        if(result['result'] == true) {
                            newTrack['url'] = result['url'];
                            inst.playlist.push(newTrack);
                            inst.updatePlaylist();
                        } else {
                            alert("Track failed to validate: " + newTrack['url'] + "\n\nAdditional processing has been halted, but tracks that were imported up until this point will need to be manually removed.");
                            break;
                        }
                    }
                }

                var newPlaylist = ev.target.result.split(/\r\n|\n|\r/);
                processPlaylist(newPlaylist);

                $('#import_m3u_modal').modal('hide');
            }
        })(inst);
        reader.readAsText(playlistFile);
    });
};
