import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { SelectmodelComponent } from './components/selectmodel/selectmodel.component';
import { HeaderComponent } from './components/header/header.component';
import { UploadDataComponent } from './components/upload-data/upload-data.component';

@NgModule({
  declarations: [
    AppComponent,
    SelectmodelComponent,
    HeaderComponent,
    UploadDataComponent
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
export class AppModule { }
