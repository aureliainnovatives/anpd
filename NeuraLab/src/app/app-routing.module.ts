import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SelectmodelComponent } from './components/selectmodel/selectmodel.component';
import { HeaderComponent } from './components/header/header.component';
import { AppComponent } from './app.component';
import { UploadDataComponent } from './components/upload-data/upload-data.component';
const routes: Routes = [
  { path: '', redirectTo: '/selectmodel', pathMatch: 'full' },
  { path: 'upload-data', component: UploadDataComponent },
  { path: 'selectmodel', component: SelectmodelComponent },
  { path: 'header', component: HeaderComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { 

}
