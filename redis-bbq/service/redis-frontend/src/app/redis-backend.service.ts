import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {catchError, map, switchMap} from "rxjs/operators";
import {Observable, of, throwError} from "rxjs";
import {v4 as uuidv4} from "uuid";

function assertNoError<T>(value: T): T {
    if (value !== null && value.constructor === Error)
        throw value;
    return value;
}

function authcheck(results: any[]): any[] {
    if (results[0] != 'OK') throw new Error('Unauthenticated!');
    return results.slice(1);
}

export interface UserInfo {
    name: string,
    dishes: string,
    dishes_cooked: string,
    watch_locations: { country: string, location: string }[]
}

export interface PartyInfo {
    name: string,
    organisator: string,
    guests: string[],
    food: string[],
    fire_id: string
}

export interface Firefighter {
    name: string;
    country: string;
    location: string;
}

export interface Fire {
    country: string;
    location: string;
    content: string;
}

export class MessageList {
    public messages: {type: string, msg: any}[] = [];

    public addMessage(type: string, msg: any) {
        this.messages.push({type, msg});
    }

    public clear() {
        this.messages = [];
    }

    public handleErrors<T>(obj: Observable<T>): Observable<T> {
        return obj.pipe(
            map(x => {
                this.clear();
                return x;
            }),
            catchError(err => {
                console.error(err);
                this.addMessage('danger', err);
                return throwError(err);
            })
        );
    }

    dismiss(i: number) {
        this.messages.splice(i, 1);
    }
}


@Injectable({
    providedIn: 'root'
})
export class RedisBackendService {

    public currentUser: string = null;
    public currentPass: string = null;
    public currentUserIsNew: boolean = false;
    public globalErrors = new MessageList();

    constructor(public http: HttpClient) {
        this.currentUser = sessionStorage.getItem('username');
        this.currentPass = sessionStorage.getItem('password');
    }

    parseRespValues(buffer: ArrayBuffer, limit = -1, pos = 0): { results: any[], pos: number } {
        let arr = new Uint8Array(buffer);
        let results = [];
        while (pos < arr.length && limit != 0) {
            let nextCRLF = pos;
            for (let i = pos; i < arr.length - 1; i++) {
                if (arr[i] == 13 && arr[i + 1] == 10) {
                    nextCRLF = i;
                    break;
                }
            }
            switch (arr[pos]) {
                case 43:
                    // Simple Strings
                    results.push(new TextDecoder().decode(arr.slice(pos + 1, nextCRLF)));
                    pos = nextCRLF + 2;
                    break;
                case 45:
                    // Errors
                    results.push(new Error(new TextDecoder().decode(arr.slice(pos + 1, nextCRLF))));
                    pos = nextCRLF + 2;
                    break;
                case 58:
                    // Integers
                    results.push(parseInt(new TextDecoder().decode(arr.slice(pos + 1, nextCRLF))));
                    pos = nextCRLF + 2;
                    break;
                case 36: {
                    // Bulk Strings
                    let length = parseInt(new TextDecoder().decode(arr.slice(pos + 1, nextCRLF)));
                    if (length < 0) {
                        results.push(null);
                        pos = nextCRLF + 2;
                    } else {
                        results.push(new TextDecoder().decode(arr.slice(nextCRLF + 2, nextCRLF + 2 + length)));
                        pos = nextCRLF + 4 + length;
                    }
                    break;
                }
                case 42: {
                    // Arrays
                    let length = parseInt(new TextDecoder().decode(arr.slice(pos + 1, nextCRLF)));
                    if (length < 0) {
                        results.push(null);
                        pos = nextCRLF + 2;
                    } else {
                        let elements = this.parseRespValues(buffer, length, nextCRLF + 2)
                        results.push(elements.results);
                        pos = elements.pos;
                    }
                    break;
                }
                default:
                    break;
            }

            limit--;
        }
        return {results, pos};
    }

    encodeRespValue(value): Uint8Array[] {
        if (value === null) {
            return [new TextEncoder().encode('$-1\r\n')];
        } else if (typeof value === 'string') {
            let enc = new TextEncoder().encode(value + '\r\n');
            return [new TextEncoder().encode('$' + (enc.length - 2) + '\r\n'), enc];
        } else if (value.constructor === Array) {
            let arr = [new TextEncoder().encode('*' + value.length + '\r\n')];
            for (let item of value) {
                arr = arr.concat(this.encodeRespValue(item));
            }
            return arr;
        } else if (typeof value == 'number') {
            return [new TextEncoder().encode(':' + value + '\r\n')];
        } else {
            throw new Error('Invalid type in RESP: ' + typeof value);
        }
    }

    join_buffers(buffers: Uint8Array[]): Uint8Array {
        let size = 0;
        for (let b of buffers) size += b.length;
        let arr = new Uint8Array(size);
        let pos = 0;
        for (let b of buffers) {
            arr.set(b, pos);
            pos += b.length;
        }
        return arr;
    }

    execute_commands(commands: any[][]): Observable<any[]> {
        let buffer = [];
        for (let command of commands) {
            for (let i = 0; i < command.length; i++) {
                if (typeof command[i] == 'number') command[i] = '' + command[i];
            }
            buffer = buffer.concat(this.encodeRespValue(command));
        }
        buffer = buffer.concat([new TextEncoder().encode('QUIT\r\n')]);
        return this.http.post("/api", this.join_buffers(buffer).buffer, {responseType: 'arraybuffer'})
            .pipe(map(data => {
                let parsed = this.parseRespValues(data).results;
                if (parsed[parsed.length-1] && parsed[parsed.length-1].constructor === Error && parsed[parsed.length-1].message.startsWith('ERR Protocol error: unbalanced quotes')) {
                    throw new Error('This website is not compatible with Chromium-based browsers. Please use Firefox instead.');
                }
                parsed = parsed.slice(parsed.findIndex(x => x.constructor !== Error || !x.message.startsWith('ERR unknown command ')), parsed.length - 1);
                return parsed;
            }));
    }

    get(key: string): Observable<any> {
        return this.execute_commands([['LEGACY_GET', key]]).pipe(map(x => assertNoError(x[0])));
    }

    newest(what: string, limit = 15): Observable<string[]> {
        return this.execute_commands([['LRANGE', 'newest:' + what, '0', limit]]).pipe(map(x => assertNoError(x[0]) || []));
    }

    addNewest(what: string, value: string): Observable<number> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['LPUSH', 'newest:' + what, value]
        ]).pipe(map(authcheck)).pipe(map(x => assertNoError(x[0]) || 0));
    }

    register(username: string, password: string): Observable<boolean> {
        return this.execute_commands([['NEWUSER', username, password]])
            .pipe(map(x => assertNoError(x[0]) == 'OK')).pipe(x => {
                if (x) {
                    this.currentUser = username;
                    this.currentPass = password;
                    sessionStorage.setItem('username', username);
                    sessionStorage.setItem('password', password);
                }
                return x;
            });
    }

    login(username: string, password: string): Observable<boolean> {
        return this.execute_commands([['AUTH', username, password]])
            .pipe(map(x => assertNoError(x[0]) == 'OK')).pipe(x => {
                if (x) {
                    this.currentUser = username;
                    this.currentPass = password;
                    sessionStorage.setItem('username', username);
                    sessionStorage.setItem('password', password);
                }
                return x;
            });
    }

    logout() {
        this.currentUser = null;
        this.currentPass = null;
        sessionStorage.removeItem('username');
        sessionStorage.removeItem('password');
    }

    getUserInfo(): Observable<UserInfo> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['LEGACY_GET', 'user:' + this.currentUser + ':name'],
            ['LEGACY_GET', 'user:' + this.currentUser + ':dishes'],
            ['LEGACY_GET', 'user:' + this.currentUser + ':dishes_cooked'],
            ['LRANGE', 'user:' + this.currentUser + ':watch_locations', '0', '-1']
        ]).pipe(map(authcheck)).pipe(map(x => {
            return {
                name: assertNoError<string>(x[0]),
                dishes: assertNoError<string>(x[1]),
                dishes_cooked: assertNoError<string>(x[2]),
                watch_locations: assertNoError<any[]>(x[3]).map(loc => JSON.parse(loc))
            };
        }));
    }

    setUserInfo(key: string, value: string): Observable<number> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['SETNX', 'user:' + this.currentUser + ':' + key, value]
        ]).pipe(map(authcheck)).pipe(map(x => assertNoError<number>(x[0])));
    }

    createParty(): Observable<string> {
        let id = uuidv4();
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['SETNX', 'party:' + id + ':organisator', this.currentUser]
        ]).pipe(map(authcheck)).pipe(map(x => {
            assertNoError(x[0]);
            return id;
        }));
    }

    getPartyInfo(id: string): Observable<PartyInfo> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['LEGACY_GET', 'party:' + id + ':name'],
            ['LEGACY_GET', 'party:' + id + ':organisator'],
            ['LEGACY_GET', 'party:' + id + ':fire_id'],
            ['SMEMBERS', 'party:' + id + ':guests'],
            ['SMEMBERS', 'party:' + id + ':food'],
        ]).pipe(map(authcheck)).pipe(map(x => {
            return {
                name: assertNoError<string>(x[0]),
                organisator: assertNoError<string>(x[1]),
                fire_id: assertNoError<string>(x[2]),
                guests: assertNoError<string[]>(x[3]),
                food: assertNoError<string[]>(x[4]),
            };
        }));
    }

    addPartyItem(party_id: string, key: string, item: string): Observable<number> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['SADD', 'party:' + party_id + ':' + key, item]
        ]).pipe(map(authcheck)).pipe(map(x => assertNoError<number>(x[0])));
    }

    setPartyItem(party_id: string, key: string, value: string): Observable<number> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['SETNX', 'party:' + party_id + ':' + key, value]
        ]).pipe(map(authcheck)).pipe(map(x => assertNoError<number>(x[0])));
    }

    createFireForParty(party_id: string, country: string, location: string, content: string): Observable<string> {
        let id = uuidv4();
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['HSETNX', 'fire:' + id, 'country', country],
            ['HSETNX', 'fire:' + id, 'location', location],
            ['HSETNX', 'fire:' + id, 'content', content],
            ['SETNX', 'fire:' + id + ':wood', 0],
            ['LPUSH', 'country:' + country + ':fires', id],
            ['SETNX', 'party:' + party_id + ':fire_id', id]
        ]).pipe(map(authcheck)).pipe(map(x => {
            assertNoError(x[0]);
            assertNoError(x[1]);
            assertNoError(x[2]);
            assertNoError(x[3]);
            assertNoError(x[4]);
            assertNoError(x[5]);
            return id;
        }));
    }

    getFireWood(fire_id: string): Observable<number> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['LEGACY_GET', 'fire:' + fire_id + ':wood']
        ]).pipe(map(authcheck)).pipe(map(x => assertNoError<number>(x[0]) || 0));
    }

    incrementFireWood(fire_id: string, amount: number): Observable<number> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['INCRBY', 'fire:' + fire_id + ':wood', amount]
        ]).pipe(map(authcheck)).pipe(map(x => assertNoError<number>(x[0]) || 0));
    }

    firealarm(fire_id: string): Observable<Firefighter[]> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['FIREALARM', 'fire:' + fire_id]
        ]).pipe(map(authcheck)).pipe(map(x => {
            let arr = assertNoError<any[]>(x[0]);
            let result = [];
            for (let i = 0; i < arr.length - 1; i += 2) {
                let obj = JSON.parse(arr[i + 1]);
                obj.name = arr[i];
                result.push(obj);
            }
            return result;
        }));
    }

    addFirefighter(country: string, location: string): Observable<number> {
        let loc = JSON.stringify({country, location});
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['HSETNX', 'country:' + country + ':firefighters', this.currentUser, loc],
        ]).pipe(map(authcheck)).pipe(switchMap((x, _) => {
            if (assertNoError(x[0])) {
                return this.execute_commands([
                    ['AUTH', this.currentUser, this.currentPass],
                    ['LPUSH', 'user:' + this.currentUser + ':watch_locations', loc]
                ]).pipe(map(authcheck)).pipe(map(x => assertNoError<number>(x[0])));
            }
            return of<number>(0);
        }));
    }

    getAlarms(): Observable<Fire[]> {
        return this.execute_commands([
            ['AUTH', this.currentUser, this.currentPass],
            ['LRANGE', 'user:' + this.currentUser + ':alarms', '0', '-1']
        ]).pipe(map(authcheck)).pipe(map(x => {
            let arr = assertNoError<string[]>(x[0]);
            let result = [];
            for (let i = 0; i + 2 < arr.length; i += 3) {
                result.push({country: arr[i], location: arr[i + 1], content: arr[i + 2]});
            }
            return result;
        }));
    }
}
