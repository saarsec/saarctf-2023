import {Component, OnInit} from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {MessageList, PartyInfo, RedisBackendService} from "../redis-backend.service";

@Component({
    selector: 'app-page-party',
    templateUrl: './page-party.component.html',
    styleUrls: ['./page-party.component.less']
})
export class PagePartyComponent implements OnInit {

    public id: string = null;
    public partyInfo: PartyInfo = null;
    public currentUserParticipating = false;
    public url = location.href;

    public food: string = "";
    public partyname: string = "";
    public fireCountry = "";
    public fireLocation = "";
    public fireContent = "";

    public errors = new MessageList();
    public errorsFire = new MessageList();

    constructor(private route: ActivatedRoute, public redis: RedisBackendService) {
    }

    ngOnInit(): void {
        this.id = this.route.snapshot.paramMap.get('id');
        this.reloadParty();
    }

    reloadParty() {
        this.errors.handleErrors(this.redis.getPartyInfo(this.id)).subscribe((info => {
            this.partyInfo = info;
            this.currentUserParticipating = this.partyInfo.guests.indexOf(this.redis.currentUser) >= 0;
        }));
    }

    participate() {
        this.errors.handleErrors(this.redis.addPartyItem(this.id, 'guests', this.redis.currentUser))
            .subscribe(_ => this.reloadParty());
    }

    addFood(food: string) {
        if (!food) {
            this.errors.addMessage('danger', 'Please add food');
            return;
        }
        this.errors.handleErrors(this.redis.addPartyItem(this.id, 'food', food)).subscribe(_ => this.reloadParty());
    }

    setName(name: string) {
        this.errors.handleErrors(this.redis.setPartyItem(this.id, 'name', name)).subscribe(_ => this.partyInfo.name = name);
    }

    createFire(country: string, location: string, content: string) {
        if (country.length != 12 || location.length != 16) {
            this.errorsFire.addMessage('danger', 'Invalid input: Country must be 12 chars long, location must be 16 chars long.');
            return;
        }
        this.errorsFire.handleErrors(this.redis.createFireForParty(this.id, country, location, content))
            .subscribe(fire_id => this.partyInfo.fire_id = fire_id);
    }

}
