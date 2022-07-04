import ncm from 'NeteaseCloudMusicApi';
import { assert, check_result } from '../utils.js';

export function is_favorite_playlist({ specialType }) {
    return specialType === 5;
}

export async function get_detail(playlist_id, cookie) {
    return check_result(await ncm.playlist_detail({
        id: playlist_id,
        cookie,
    })).playlist;
}

export async function get_dynamic_detail(playlist_id, cookie) {
    return check_result(await ncm.playlist_detail_dynamic({
        id: playlist_id,
        cookie,
    }));
}

import { Task } from "./base.js";
import { confirm_once, make_index, make_index_from_lists, get_map_diff, get_map_itsect } from "../utils.js";
import { song_to_string, song_to_url } from "../types.js";

function mkindex(playlist) {
    return make_index(playlist, 'id');
}

function mkindex_list(playlists) {
    return make_index_from_lists(playlists, 'tracks', 'id');
}

export class pull_all_playlists extends Task {
    name = 'Update Playlist from Remote';
    async check(data) {
        let playlists = [];
        const { account: { id: uid }, cookie } = data;
        for (let more=true; more; ) {
            const res = check_result(await ncm.user_playlist({ uid, cookie, offset: playlists.length }));
            playlists = playlists.concat(res.playlist);
            more = res.more;
        }
        for (const i in playlists) {
            playlists[i] = await get_detail(playlists[i].id, cookie);
        }
        this.playlists = playlists;
        if (data.hasOwnProperty('playlists')) {
            const old_playlists = mkindex_list(data.playlists);
            const new_playlists = mkindex_list(playlists);
            const missing = get_map_diff(old_playlists, new_playlists);
            if (missing.size > 0) {
                this.log('Songs that are removed in the remote:');
                for (const song of missing.values()) {
                    this.log('\t' + song_to_string(song));
                    this.log('\t\t' + song_to_url(song));
                }
                return false;
            }
        }
        return true;
    }
    async action(data) {
        data.playlists = this.playlists;
        return data;
    }
}

/**
 * Caution! This has no sanity check
 */
export class pull_playlist extends Task {
    constructor(pid) {
        super();
        this.pid = pid;
        this.name = `Pull Playlist ${pid}`;
    }
    async action(data) {
        let ptr = null;
        for (const [i, v] of data.playlists.entries()) {
            if (v.id === this.pid) {
                ptr = i;
                break;
            }
        }
        assert(ptr !== null);
        data.playlists[ptr] = await get_detail(this.pid, data.cookie);
        return data;
    }
}

export class remove_inbox_dup extends Task {
    name = 'Inbox Dedup';
    async check(data) {
        const { playlists, account: { id: uid } } = data;
        let fav = null;
        const rest = [];
        for (const p of playlists) {
            if (p.creator.userId !== uid) continue;
            if (is_favorite_playlist(p)) {
                fav = p;
            } else {
                rest.push(p);
            }
        }
        assert(fav !== null);
        const dup = get_map_itsect(mkindex(fav.tracks), mkindex_list(rest));
        this.fav = fav;
        this.dup = dup;
        if (dup.size > 0) {
            this.log('Songs that can be removed from heart list:');
            for (const song of dup.values()) {
                this.log('\t' + song_to_string(song));
                this.log('\t\t' + song_to_url(song));
            }
            return false;
        } else return true;
    }
    async confirm() {
        return confirm_once();
    }
    async action(data) {
        if (this.dup.size > 0) {
            /*
            for (const v of this.dup.values()) {
                const res = check_result(await ncm.like({
                    id: v.id,
                    like: false,
                    cookie: data.cookie,
                }));
                this.log(res);
            }
            */
            const res = await ncm.playlist_tracks({
                op: 'del',
                pid: this.fav.id,
                tracks: Array.from(this.dup.values()).map(x=>x.id).join(','),
                cookie: data.cookie,
            });
            assert.equal(res.status, 200);
            data = await (new pull_playlist(this.fav.id)).start(data);
        }
        return data;
    }
}

export class test_year_list_exclusive extends Task {
    name='Test Year List Exclusive';
    async check(data) {
        const { account: { id: uid }, playlists } = data;
        const arr = [];
        for (const pl of playlists) {
            if (pl.creator.userId !== uid) continue;
            if (/\b\d{4}\b/.test(pl.name)) {
                arr.push(pl);
            }
        }
        const id_map = new Map;
        for (const pl of arr) {
            for (const song of pl.tracks) {
                if (id_map.has(song.id)) {
                    id_map.get(song.id).push(pl);
                } else {
                    id_map.set(song.id, [song, pl]);
                }
            }
        }
        const dups = [];
        for (const [i, v] of id_map) {
            if (v.length > 2) {
                dups.push(v);
            }
        }
        if (dups.length > 0) {
            this.log('Some songs are duplicated:');
            for (const song_list of dups) {
                this.log(`Song "${song_list[0].name}" occurs in:`);
                for (const pl of song_list.slice(1)) {
                    this.log(`\t${pl.name}`);
                }
            }
            return false;
        }
        return true;
    }
    async confirm() {
        return await confirm_once();
    }
}

export class test_level5_included extends Task {
    name='Test Level 5 Included';
    async check(data) {
        const { account: { id: uid }, playlists } = data;
        let level5 = null;
        let rest = [];
        for (const pl of playlists) {
            if (pl.creator.userId !== uid) continue;
            if (pl.name === 'Level 5') {
                level5 = pl;
            } else {
                rest.push(pl);
            }
        }
        assert.notEqual(level5, null);
        level5 = mkindex(level5.tracks);
        rest = mkindex_list(rest);
        this.not_included = get_map_diff(level5, rest);
        if (this.not_included.size > 0) {
            this.log('Some songs in Level 5 are not included in other playlists:');
            for (const song of this.not_included.values()) {
                this.log(`\t${song.name} [ncm${song.id}]`);
            }
            return false;
        }
        return true;
    }
    async confirm() {
        return await confirm_once();
    }
}
