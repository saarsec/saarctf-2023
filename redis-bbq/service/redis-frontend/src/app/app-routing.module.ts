import {NgModule} from '@angular/core';
import {Routes, RouterModule} from '@angular/router';
import {PageFrontComponent} from "./page-front/page-front.component";
import {PageUserComponent} from "./page-user/page-user.component";
import {PagePartyComponent} from "./page-party/page-party.component";

const routes: Routes = [
    {path: '', component: PageFrontComponent},
    {path: 'home', component: PageUserComponent},
    {path: 'party/:id', component: PagePartyComponent}
];

@NgModule({
    imports: [RouterModule.forRoot(routes, { useHash: true })],
    exports: [RouterModule]
})
export class AppRoutingModule {
}
