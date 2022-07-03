import ncm from 'NeteaseCloudMusicApi';
import { assert, check_result, confirm_once, make_index_from_lists } from '../utils.js';

// Deprecated since all the info needed are in the list
export async function get_detail(id, cookie) {
    if (typeof id === 'number') {
        id = [ id ];
    }
    return check_result(await ncm.user_cloud_detail({
        id: id.join(','),
        cookie,
    })).data;
}

/**
 * 
 * @param {String} name Filename in the NCM storage
 * @param {Blob} data The music data read by fs.readFileSync
 * @param {String} cookie User cookie
 * @returns 
 */
export async function upload_song(name, data, cookie) {
    let res = check_result(await ncm.cloud({
      songFile: { name, data },
      cookie,
    }));
    return res;
}

import { readFile } from 'fs/promises';
import path from 'path';

export async function upload_song_from_path(file_path, cookie) {
    return upload_song(
        path.basename(file_path),
        await readFile(file_path),
        cookie,
    );
}

import { Task } from "./base.js";
import { current_path, make_index, get_map_diff } from "../utils.js";
import { readdir } from "fs/promises";


export class pull_remote extends Task {
    name = 'Pull Remote Cloud Song List';
    async check(data) {
        let cloud_list = [];
        for(let more=true; more; ) {
            let res = check_result(await ncm.user_cloud({
                cookie: data.cookie,
                offset: cloud_list.length,
            }));
            cloud_list = cloud_list.concat(res.data);
            more = res.hasMore;
        }
        this.cloud_list = cloud_list;
        if (data.hasOwnProperty('cloud_list')) {
            const local = make_index(data.cloud_list, 'songId');
            const remote = make_index(this.cloud_list, 'songId');
            const missing = get_map_diff(local, remote);
            if (missing.size > 0) {
                this.log('Some songs are missing in the remote cloud list:');
                for (const cloud_song of missing.values()) {
                    this.log(`\t${cloud_song.songName}, file=${cloud_song.fileName}, id=${cloud_song.songId}`);
                }
                return false;
            }
        }
        return true;
    }
    async action(data) {
        data.cloud_list = this.cloud_list;
        return data;
    }
}

export function lib_path() {
    return current_path() + '/music';
}

export class get_local_file extends Task{
    async action() {
        const files = await readdir(lib_path());
        return files.map((fileName) => ({
            id: Number.parseInt(fileName.match(/\[ncm(\d+)\]/)[1]),
            fileName,
        }));
    }
}

async function get_local_file_map() {
    const task = new get_local_file();
    return make_index(await task.start(), 'id');
}

/**
 * Assuming that the local cloud list is up to date with the remote
 */
export class sync_local_remove extends Task {
    name = 'Remove Cloud Music';
    async check(data) {
        const local_file = await get_local_file_map();
        const remote_file = make_index(data.cloud_list, 'songId');
        this.missing = new Map;
        for(const [i, v] of get_map_diff(remote_file, local_file)) {
            if (v.fileName.match(/\[ncm(\d+)\]/) !== null) {
                this.missing.set(i, v);
            } else {
                this.log(`${v.songName} [ncm${v.songId}] is not locally available`);
            }
        }
        if (this.missing.size === 0) return true;
        this.log('Some songs have been deleted from local:');
        for(const [i, v] of this.missing) {
            this.log(`\t(${v.songId}) filename=${v.fileName}`);
        }
        return false;
    }
    async action(data) {
        if (this.missing.size === 0) return data;
        let res;
        try {
            res = await ncm.user_cloud_del({
                id: Array.from(this.missing.values()).map(x=>x.songId).join(','),
                cookie: data.cookie,
            });
        } catch(err) {
            this.log(err);
            res = err;
        }
        res = res.body;
        this.log('Delete succeeded:' + res.succIds.join(','));
        this.log('Delete failed: ' + res.failIds.join(','));
        return data;
    }
}

export class sync_local_add extends Task {
    name = 'Upload Local Music';
    async check(data) {
        const local_file = await get_local_file_map();
        const remote_file = make_index(data.cloud_list, 'songId');
        this.new_files = get_map_diff(local_file, remote_file);
        if (this.new_files.size === 0) return true;
        this.log('New songs from local to be added:');
        for(const [i, v] of this.new_files) {
            this.log(`\tfilename=${v.fileName}`);
        }
        return false;
    }
    async confirm() {
        return await confirm_once();
    }
    async action(data) {
        if (this.new_files.size === 0) return data;
        for (const [id, obj] of this.new_files) {
            this.log('Uploading', obj.fileName);
            const { privateCloud } = check_result(await ncm.cloud_flac({
                cookie: data.cookie,
                songFile: {
                    name: obj.fileName,
                    data: await readFile(lib_path() + '/' + obj.fileName),
                },
            }));
            this.log('OK');
            if (privateCloud.songId !== obj.id) {
                this.log('Now modifying songId from', privateCloud.songId, 'to', obj.id);
                let res = check_result(await ncm.cloud_match({
                    uid: data.account.uid,
                    sid: privateCloud.songId,
                    asid: obj.id,
                    cookie: data.cookie,
                }));
            }
        }
        return data;
    }
}

export class test_unused_cloud_music extends Task {
    name = 'Unused Cloud Music';
    async check(data) {
        const { playlists, cloud_list } = data;
        const pl_songs = make_index_from_lists(playlists, 'tracks', 'id');
        const cloud_songs = make_index(cloud_list, 'songId');
        this.unused_songs = get_map_diff(cloud_songs, pl_songs);
        if (this.unused_songs.size > 0) {
            this.log('Some songs in the cloud list is not used in playlists:');
            for (const song of this.unused_songs.values()) {
                this.log(`\t${song.songName} [ncm${song.songId}]`);
                this.log(`\t\t${song.fileName}`);
            }
            return false;
        }
        return true;
    }
    async confirm() {
        return confirm_once();
    }
}
