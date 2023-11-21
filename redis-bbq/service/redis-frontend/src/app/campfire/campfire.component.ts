import {Component, Input, OnInit} from '@angular/core';
import {Firefighter, MessageList, RedisBackendService} from "../redis-backend.service";

@Component({
    selector: 'app-campfire',
    templateUrl: './campfire.component.html',
    styleUrls: ['./campfire.component.less']
})
export class CampfireComponent implements OnInit {

    @Input()
    public fire_id: string;

    public wood: number = null;
    public firefighters: Firefighter[] = null;

    public errors = new MessageList();

    constructor(public redis: RedisBackendService) {
    }

    ngOnInit(): void {
        this.errors.handleErrors(this.redis.getFireWood(this.fire_id)).subscribe(wood => this.wood = wood);
    }

    addWood() {
        let amount = Math.floor(Math.random() * 20) + 12;
        this.errors.handleErrors(this.redis.incrementFireWood(this.fire_id, amount))
            .subscribe(wood => {
                this.wood = wood;
                setTimeout(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 1);
            });
    }

    firealarm() {
        this.errors.handleErrors(this.redis.firealarm(this.fire_id)).subscribe(ff => this.firefighters = ff);
    }

    min(a: number, b: number) {
        return Math.min(a, b);
    }
}
