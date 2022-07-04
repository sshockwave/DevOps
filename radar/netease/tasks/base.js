import { readFile, writeFile, confirm_twice, assert } from '../utils.js';

export class Task{
    name = 'Default';
    log(...msg) {
        console.log(`[${this.name}]`, ...msg);
    }
    async check(data) {
        return true;
    }
    async confirm(data) {
        return await confirm_twice();
    }
    async action(data) {
        return data;
    }
    async start(data){
        this.log('Starting');
        let preflight_check = await this.check(data);
        if (!preflight_check) {
            if (await this.confirm(data)) {
                preflight_check = true;
            }
        }
        if (preflight_check) {
            data = await this.action(data);
            this.log('Finished');
            return data;
        } else {
            this.log('Canceled due to failed checks.');
            return false;
        }
    }
    pipe(task) {
        return (new Series([this], 'Pipe')).pipe(task);
    }
}

export class Series extends Task {
    async start(data) {
        for (let task of this.tasks) {
            data = await task.start(data);
            if (data === false) {
                return false;
            }
        }
    }
    constructor(tasks=[], name='Series') {
        super();
        this.name = name;
        this.tasks = tasks;
    }
    pipe(task) {
        this.tasks.push(task);
        return this;
    }
}

export class Wrapper extends Task {
    name = 'Function';
    async action(data) {
        return await this.fn(data);
    }
    constructor(fn) {
        super();
        this.fn = fn;
    }
}

export class LoadJSONFile extends Task {
    name = 'Load JSON File';
    async action() {
        return JSON.parse(await readFile(this.file_path));
    }
    constructor(file_path) {
        super();
        this.file_path = file_path;
    }
}

export class SaveJSONFile extends Task {
    name = 'Save JSON File';
    async action(data) {
        await writeFile(this.file_path, JSON.stringify(data));
        return data;
    }
    constructor(file_path) {
        super();
        this.file_path = file_path;
    }
}
