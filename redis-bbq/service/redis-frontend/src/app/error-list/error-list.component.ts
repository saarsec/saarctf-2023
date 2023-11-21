import {Component, Input, OnInit} from '@angular/core';
import {MessageList} from "../redis-backend.service";

@Component({
    selector: 'app-error-list',
    templateUrl: './error-list.component.html',
    styleUrls: ['./error-list.component.less']
})
export class ErrorListComponent implements OnInit {

    @Input()
    list: MessageList;

    constructor() {
    }

    ngOnInit(): void {
    }

}
