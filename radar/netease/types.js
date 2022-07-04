const profile_type = {
    userId: Number,
    nickname: String,
};

const account_type = {
    id: Number,
};

const album_type = {
    id: Number,
    name: String,
};

const song_type = {
    id: Number,
    name: String,
    ar: [],
    al: album_type,
};

const playlist_type = {
    id: Number,
    name: String,
    creator: profile_type,
    tracks: [song_type],
};

const cloud_song_type = {
    simpleSong: song_type,
    fileSize: Number,
    album: String,
    artist: String,
    songId: Number,
    songName: String,
    fileName: String,
};

export function song_to_string(song) {
    return `"${song.name}"(${song.id}; from ${song.al.name})`;
}

export function song_to_url(song) {
    return `https://music.163.com/#/song?id=${song.id}`;
}

export function log_song_list(songs) {
    for (const song of songs) {
        console.log(song_to_string(song));
        console.log('\t' + song_to_url(song));
    }
}
