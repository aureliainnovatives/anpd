import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { SystemListComponent } from './components/system-list/system-list.component';
import { LicenseGeneratorComponent } from './components/license-generator/license-generator.component';
import { AuthGuard } from './guards/auth.guard';
import { LoginGuard } from './guards/login.guard';

const routes: Routes = [
  { 
    path: 'login', 
    component: LoginComponent,
    canActivate: [LoginGuard]
  },
  { 
    path: 'dashboard', 
    component: DashboardComponent,
    canActivate: [AuthGuard]
  },
  { 
    path: 'systems', 
    component: SystemListComponent,
    canActivate: [AuthGuard]
  },
  { 
    path: 'generate-license/:id', 
    component: LicenseGeneratorComponent,
    canActivate: [AuthGuard]
  },
  { 
    path: '', 
    redirectTo: '/dashboard', 
    pathMatch: 'full' 
  },
  { 
    path: '**', 
    redirectTo: '/dashboard' 
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
