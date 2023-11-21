import {Component} from '@angular/core';
import {RedisBackendService} from "./redis-backend.service";
import {NavigationStart, Router} from "@angular/router";

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.less']
})
export class AppComponent {
    title = 'redis-frontend';

    constructor(public redis: RedisBackendService, public router: Router) {
        this.router.events.subscribe(event => {
            if (event instanceof NavigationStart) {
                let url = event.url.slice(1);
                let p = url.indexOf('/');
                if (p > 0) url = url.substr(0, p);
                document.body.dataset['page'] = url;
            }
        });
    }

    logout() {
        this.redis.logout();
        this.router.navigate(['/']);
    }

}
