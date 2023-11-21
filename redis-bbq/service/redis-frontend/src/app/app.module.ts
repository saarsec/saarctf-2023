import {BrowserModule} from '@angular/platform-browser';
import {NgModule} from '@angular/core';

import {AppRoutingModule} from './app-routing.module';
import {AppComponent} from './app.component';
import {PageFrontComponent} from './page-front/page-front.component';
import {PageUserComponent} from './page-user/page-user.component';
import {PagePartyComponent} from './page-party/page-party.component';
import {CampfireComponent} from './campfire/campfire.component';
import {HttpClientModule} from "@angular/common/http";
import {FormsModule} from "@angular/forms";
import { ErrorListComponent } from './error-list/error-list.component';

@NgModule({
    declarations: [
        AppComponent,
        PageFrontComponent,
        PageUserComponent,
        PagePartyComponent,
        CampfireComponent,
        ErrorListComponent
    ],
    imports: [
        BrowserModule,
        AppRoutingModule,
        HttpClientModule,
        FormsModule
    ],
    providers: [],
    bootstrap: [AppComponent]
})
export class AppModule {
}
