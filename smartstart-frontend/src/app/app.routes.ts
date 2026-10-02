import { Routes } from '@angular/router';
import { Login } from './pages/auth/login/login';
import { authGuard } from './core/guards/auth-guard';
import { Register } from './pages/auth/register/register';
import { OnboardingComponent } from './pages/investor/onboarding/onboarding';
import { InvestorHistory } from './pages/investor/history/history';
// ── ML Models ──
import { GrowthComponent } from './pages/growth/growth.component';
import { RiskComponent } from './pages/risk/risk.component';
import { DetectionComponent } from './pages/detection/detection.component';
import { CompanyComponent } from './pages/Startuper/onboarding/company.component';
import { DashboardStartuper } from './pages/Startuper/dashboard-startuper/dashboard-startuper';
import { DashboardCeo } from './pages/Startuper/dashboard-ceo/dashboard-ceo';
import { CompanyAnalysisComponent } from './pages/investor/company-analysis/company-analysis';
import { CryptoAnalysisComponent } from './pages/investor/crypto-analysis/crypto-analysis';
import { InvestiqAnalyzerComponent } from './pages/Startuper/invest-analyzer/investiq-analyzer.component';
import { Dashboard as DashboardInvestor } from './pages/investor/dashboard/dashboard';

export const routes: Routes = [
  { path: 'login', component: Login },
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'register', component: Register },

  // ── Onboarding ──
  { path: 'investor/onboarding', component: OnboardingComponent, canActivate: [authGuard] },
  { path: 'startuper/onboarding', component: CompanyComponent, canActivate: [authGuard] },

  // ── Startuper / CEO ──
  // ── Startuper ──
  { path: 'dashboard/startuper', component: DashboardStartuper, canActivate: [authGuard] },
  { path: 'dashboard/startuper/ceo', component: DashboardCeo, canActivate: [authGuard] },
  { path: 'dashboard/invest-analyzer', component: InvestiqAnalyzerComponent, canActivate: [authGuard] },
  // ── Investor ──
  { path: 'dashboard/investor', component: DashboardInvestor, canActivate: [authGuard] },
  { path: 'dashboard/analyze', component: CompanyAnalysisComponent, canActivate: [authGuard] },
  { path: 'dashboard/crypto-analysis', component: CryptoAnalysisComponent, canActivate: [authGuard] },
  { path: 'investor/history', component: InvestorHistory, canActivate: [authGuard] },

  // ── ML ──
  { path: 'dashboard/growth', component: GrowthComponent, canActivate: [authGuard] },
  { path: 'dashboard/risk', component: RiskComponent, canActivate: [authGuard] },
  { path: 'dashboard/detection', component: DetectionComponent, canActivate: [authGuard] },
  { path: 'dashboard/investor/history', component: InvestorHistory, canActivate: [authGuard] },
];