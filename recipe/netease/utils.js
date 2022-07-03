import { strict as assert } from 'assert';
import { readFile as fs_readFile, writeFile as fs_writeFile } from 'fs/promises';

export { assert };

export function check_result(result) {
    assert(result.status >= 200 && result.status < 300);
    assert(result.body.code >= 200 && result.body.code < 300);
    delete result.body.code;
    return result.body;
}

import { dirname } from 'path';
import { fileURLToPath } from 'url';

export function current_path() {
    return dirname(fileURLToPath(import.meta.url));
}

export async function readFile(file_path) {
    return fs_readFile(current_path() + file_path);
}

export async function writeFile(file_path, data) {
    return fs_writeFile(current_path() + file_path, data);
}

import inquirer from 'inquirer';
export async function confirm_twice(confirm_text='confirm') {
    let answers = await inquirer.prompt([
        {
            type: 'confirm',
            name: 'first',
            message: 'Is this intended?',
            default: false,
        },
    ]);
    if (answers.first) {
        let answers = await inquirer.prompt([
            {
                type: 'input',
                name: 'second',
                message: `Confirm again by typing "${confirm_text}"`,
            },
        ]);
        if (answers.second === confirm_text) {
            return true;
        }
    }
    return false;
}

export async function confirm_once() {
    let answers = await inquirer.prompt([
        {
            type: 'confirm',
            name: 'first',
            message: 'Is this ok?',
            default: true,
        },
    ]);
    return answers.first;
}

export function make_index(obj_list, key, enforce_unique=false) {
    const c = new Map;
    for (const obj of obj_list) {
        if (enforce_unique) {
            assert(!c.has(obj[key]));
        }
        c.set(obj[key], obj);
    }
    return c;
}

export function make_index_from_lists(list_list, key1, key2) {
    const c = new Map;
    for (const obj1 of list_list) {
        for (const obj2 of obj1[key1]) {
            c.set(obj2[key2], obj2);
        }
    }
    return c;
}

export function get_map_diff(a, b) {
    const c = new Map;
    for (const [i, v] of a) {
        if (!b.has(i)) {
            c.set(i, v);
        }
    }
    return c;
}

export function get_map_itsect(a, b) {
    const c = new Map;
    for (const [i, v] of a) {
        if (b.has(i)) {
            c.set(i, v);
        }
    }
    return c;
}
