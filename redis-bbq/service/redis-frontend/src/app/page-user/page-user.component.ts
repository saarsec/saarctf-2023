import {Component, OnDestroy, OnInit} from '@angular/core';
import {MessageList, RedisBackendService, UserInfo} from "../redis-backend.service";
import {Router} from "@angular/router";

@Component({
    selector: 'app-page-user',
    templateUrl: './page-user.component.html',
    styleUrls: ['./page-user.component.less']
})
export class PageUserComponent implements OnInit, OnDestroy {

    public userInfo: UserInfo = null;

    public dishes = "";
    public dishes_cooked = "";

    public ffCountry = "";
    public ffLocation = "";
    public ffInterval = null;
    public alarms = [];

    public errors = new MessageList();
    public errorFireFighter = new MessageList();

    constructor(public redis: RedisBackendService, public router: Router) {
    }

    ngOnInit(): void {
        if (!this.redis.currentUser) {
            this.router.navigate(['']);
        }
        this.refresh();
    }

    ngOnDestroy() {
        if (this.ffInterval !== null) {
            clearInterval(this.ffInterval);
        }
    }

    refresh() {
        this.errors.handleErrors(this.redis.getUserInfo()).subscribe(info => {
            this.userInfo = info;
            if (this.userInfo.watch_locations && this.ffInterval === null) {
                this.ffInterval = setInterval(() => {
                    this.checkForFires();
                }, 5000);
                this.checkForFires();
            }
        });
    }

    store(key, value) {
        this.errors.handleErrors(this.redis.setUserInfo(key, value)).subscribe(_ => this.refresh());
    }

    newParty() {
        this.errors.handleErrors(this.redis.createParty()).subscribe(party_id => {
            this.redis.globalErrors.addMessage('success', 'Welcome to the party! Please share its link with your guests!');
            this.router.navigate(['party/' + party_id]);
        });
    }

    announceMe() {
        this.errors.handleErrors(this.redis.addNewest('users', this.redis.currentUser))
            .subscribe(_ => this.redis.currentUserIsNew = false);
    }

    registerFirefighter(country: string, location: string) {
        if (country.length != 12 || location.length != 16) {
            this.errorFireFighter.addMessage('danger', 'Invalid input: Country must be 12 chars long, location must be 16 chars long.');
            return;
        }
        this.errorFireFighter.handleErrors(this.redis.addFirefighter(country, location))
            .subscribe(_ => this.refresh());
    }

    checkForFires() {
        this.errorFireFighter.handleErrors(this.redis.getAlarms()).subscribe(alarms => {
            if (this.alarms.length < alarms.length) {
                // TODO
            }
            this.alarms = alarms;
        })
    }
}
