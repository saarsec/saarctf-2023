import {Component, OnInit} from '@angular/core';
import {MessageList, RedisBackendService} from "../redis-backend.service";
import {Router} from "@angular/router";

@Component({
    selector: 'app-page-front',
    templateUrl: './page-front.component.html',
    styleUrls: ['./page-front.component.less']
})
export class PageFrontComponent implements OnInit {

    public newestUsers = [];
    public newestCountries = [];

    public username: string;
    public password: string;
    public errors = new MessageList();
    public errorNewestUsers = new MessageList();
    public errorNewestCountries = new MessageList();

    constructor(public redis: RedisBackendService, public router: Router) {
    }

    ngOnInit(): void {
        console.log(this.redis);
        this.errorNewestUsers.handleErrors(this.redis.newest('users'))
            .subscribe(users => this.newestUsers = users);
        this.errorNewestCountries.handleErrors(this.redis.newest('countries'))
            .subscribe(countries => this.newestCountries = countries);
    }

    login() {
        this.errors.handleErrors(this.redis.login(this.username, this.password)).subscribe(ok => {
            if (ok) {
                this.redis.currentUserIsNew = false;
                this.router.navigate(['home']);
            }
        });
    }

    register() {
        this.redis.register(this.username, this.password).subscribe(ok => {
            if (ok) {
                this.redis.currentUserIsNew = true;
                this.redis.globalErrors.addMessage('success', 'Welcome, ' + this.username + '! You can now join partys, or start your own! Please respect the fire protection regulations.');
                this.router.navigate(['home']);
            }
        });
    }

}
