function PlaylistEditor(baseUrl) {
    this.baseUrl = baseUrl;
    this.displayRewrites = [];
}

PlaylistEditor.prototype.init = function() {
    this.initPlaylist();
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
    var inst = this;

    for(let i = 0; i < existingTracks.length; i++) {
        this.playlist.push({
            'track_id': existingTracks[i]['id'],
            'url': existingTracks[i]['url'],
        });

        // asynchronously load metadata for this track
        let existingId = existingTracks[i]['id'];
        $.ajax({
            url: this.baseUrl + "/api/validate_track",
            dataType: "json",
            data: {
                'url': existingTracks[i]['url'],
            },
            success: function(data) {
                if(data['result'] == true) {
                    // we need to walk through the entire playlist because the
                    // order may have changed between the initial load and this
                    // callback firing
                    for(var j = 0; j < inst.playlist.length; j++) {
                        if(inst.playlist[j]['track_id'] == existingId) {
                            Object.assign(inst.playlist[j], data);
                        }
                    }
                    inst.updatePlaylist();
                }
            },
        });
    }

    this.updatePlaylist();
};

PlaylistEditor.prototype.updatePlaylist = function() {
    $("table#playlist tbody tr").remove();
    for(var i = 0; i < this.playlist.length; i++) {
        var result = this.playlist[i];
        result['id'] = i;
        $("table#playlist tbody").append(this.renderTrackRow(
            result, 'playlist'));
    }
};

PlaylistEditor.prototype.renderTrackRow = function(track, context) {
    var row = $('<tr>');
    var cols = [];

    if(context == 'playlist') {
        cols.push('artist', 'title', 'album', 'label', 'length', 'url');

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

        cols.push('artist', 'title', 'album', 'label', 'length', 'url');

        row.attr('data-url', track['url']);
    }

    // main text entries

    for(let c in cols) {
        var td = $('<td>');

        var colName = cols[c];
        td.addClass(colName);

        if(colName == 'length') {
            let minutes = Math.floor(track[colName] / 60);
            let seconds = track[colName] % 60;
            if(!Number.isNaN(minutes) && !Number.isNaN(seconds)) {
                td.text(minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0'));
            }
        } else if(colName == 'url') {
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
                inst.playlist.push(data);
                inst.updatePlaylist();
            } else {
                console.log("Track failed to validate");
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
            for(var i = 0; i < data['hits'].length; i++) {
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
