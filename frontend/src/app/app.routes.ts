import { Routes, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthStore } from './core/auth-store';
import { LoginComponent } from './pages/login.component';
import { RunsComponent } from './pages/runs.component';
import { RunDetailComponent } from './pages/run-detail.component';
import { ApprovalsComponent } from './pages/approvals.component';
import { AgentsComponent } from './pages/agents.component';
import { TenantsComponent } from './pages/tenants.component';
import { PlaygroundComponent } from './pages/playground.component';
import { PromptsComponent } from './pages/prompts.component';
import { ExperimentsComponent } from './pages/experiments.component';
import { BuilderComponent } from './pages/builder.component';
import { UsageComponent } from './pages/usage.component';

const connected = () => inject(AuthStore).connected || inject(Router).createUrlTree(['/login']);

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'runs', component: RunsComponent, canActivate: [() => connected()] },
  { path: 'runs/:id', component: RunDetailComponent, canActivate: [() => connected()] },
  { path: 'approvals', component: ApprovalsComponent, canActivate: [() => connected()] },
  { path: 'agents', component: AgentsComponent, canActivate: [() => connected()] },
  { path: 'tenants', component: TenantsComponent, canActivate: [() => connected()] },
  { path: 'playground', component: PlaygroundComponent, canActivate: [() => connected()] },
  { path: 'prompts', component: PromptsComponent, canActivate: [() => connected()] },
  { path: 'experiments', component: ExperimentsComponent, canActivate: [() => connected()] },
  { path: 'builder', component: BuilderComponent, canActivate: [() => connected()] },
  { path: 'usage', component: UsageComponent, canActivate: [() => connected()] },
  { path: '', redirectTo: 'runs', pathMatch: 'full' },
  { path: '**', redirectTo: 'runs' },
];
