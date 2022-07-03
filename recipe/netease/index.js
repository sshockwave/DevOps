import * as tasks from './tasks/base.js';
import * as login from './tasks/login.js';
import * as playlist from './tasks/playlist.js';
import * as cloud from './tasks/cloud.js';

export async function run_pipeline(uid, cookie) {
    const file_path = '/data/metadata.json';
    let task = (new tasks.LoadJSONFile(file_path))
        .pipe(new login.get_cookie())
        .pipe(new playlist.pull_all_playlists())
        .pipe(new playlist.test_year_list_exclusive())
        .pipe(new playlist.remove_inbox_dup())
        .pipe(new playlist.test_level5_included())
        .pipe(new cloud.pull_remote())
        .pipe(new cloud.sync_local_remove())
        .pipe(new cloud.sync_local_add())
        .pipe(new cloud.pull_remote())
        .pipe(new cloud.test_unused_cloud_music())
        .pipe(new tasks.SaveJSONFile(file_path));
    await task.start();
}

async function main() {
    return await run_pipeline();
    const cookie = await login.get_cookie();
    const account = await login.account_info(cookie);
    const { id: uid } = account;
    console.log(uid);
    return tasks.main(uid, cookie);
    let pls = await playlist.get_playlists(uid, cookie);
    console.log(pls[1]);
    return;
    let det = await cloud.get_list(cookie);
    let cloud_song = det[0];
    console.log(cloud_song);
    let cloud_det = await cloud.get_detail(cloud_song.songId, cookie);
    console.log(cloud_det);
}

export default main
main().catch((err)=>{
    console.log(err);
});
