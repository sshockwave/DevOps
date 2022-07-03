import ncm from 'NeteaseCloudMusicApi';
import { check_result } from '../utils.js';
import { Task } from "./base.js";

const credential = {
    email: 'k820000503@163.com',
    password: 'Lt031513@hum',
}

export class get_cookie extends Task {
    name = 'Get Cookie';
    async action(data) {
        let self=this;
        async function fetch_info() {
            const res = check_result(await ncm.user_account({
                cookie: data.cookie,
            }));
            if (res.account === null) {
                throw "Cookie invalid.";
            }
            data.cookie = res.cookie || data.cookie;
            data.account = res.account;
            data.profile = res.profile;
        }
        try {
            await fetch_info();
        } catch (e) {
            this.log(e);
            data.cookie = check_result(await ncm.login(credential)).cookie;
            await fetch_info();
        }
        return data;
    }
}
