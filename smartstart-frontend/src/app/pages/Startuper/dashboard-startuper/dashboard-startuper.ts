import {
  AfterViewChecked, Component, ElementRef,
  inject, signal, ViewChild,
  ViewEncapsulation
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { StartupDashboardService } from '../../../core/services/startup-dashboard.service';
import { ChatMessage } from '../../../core/models/startup-dashboard.models';

@Component({
  selector: 'app-dashboard-startuper',
  standalone: true,
  encapsulation: ViewEncapsulation.None,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './dashboard-startuper.html',
  styleUrls: ['./dashboard-startuper.css'],
})
export class DashboardStartuper implements AfterViewChecked {

  private readonly dashService = inject(StartupDashboardService);

  @ViewChild('chatBox') private chatBox!: ElementRef<HTMLDivElement>;

  aiLoading = signal(false);
  aiError = signal<string | null>(null);
  messages = signal<ChatMessage[]>([{
    role: 'ai',
    text: 'Bonjour ! Je suis votre assistant IA SmartStart. Posez-moi une question sur votre entreprise ou sur vos analyses.',
    timestamp: new Date()
  }]);
  customPrompt = '';
  private shouldScroll = false;

  ngAfterViewChecked(): void {
    if (this.shouldScroll && this.chatBox) {
      this.chatBox.nativeElement.scrollTop = this.chatBox.nativeElement.scrollHeight;
      this.shouldScroll = false;
    }
  }

  // ── AI Assistant ───────────────────────────────────────────
  sendCustomPrompt(): void {
    const msg = this.customPrompt.trim();
    if (!msg || this.aiLoading()) return;
    this.customPrompt = '';
    this.pushMessage('user', msg);
    this.callAI(msg, 'custom');
  }

  triggerAI(action: 'summary' | 'career_advice'): void {
    const msgMap = {
      summary: 'Donne-moi un résumé de mon entreprise.',
      career_advice: 'Quels conseils stratégiques pour développer mon entreprise et attirer des investisseurs ?',
    };
    this.pushMessage('user', msgMap[action]);
    this.callAI(msgMap[action], action);
  }

  private callAI(message: string, action: 'summary' | 'career_advice' | 'custom'): void {
    this.aiLoading.set(true);
    this.aiError.set(null);

    this.dashService.askAI({ message, action }).subscribe({
      next: r => {
        this.pushMessage('ai', r.result);
        this.aiLoading.set(false);
      },
      error: err => {
        let errMsg = 'Le service IA est indisponible.';
        if (err.status === 403) {
          errMsg = 'Erreur 403 : permission refusée (rôle STARTUPER requis ou webhook n8n).';
        } else if (err.status === 401) {
          errMsg = 'Erreur 401 : token expiré. Reconnectez-vous.';
        } else if (err.status === 0 || err.status === 504) {
          errMsg = "Impossible de joindre n8n. Vérifiez que le workflow est actif et que l'URL du webhook est correcte.";
        }
        this.aiError.set(errMsg);
        this.aiLoading.set(false);
      },
    });
  }

  private pushMessage(role: 'user' | 'ai', text: string): void {
    this.messages.update(msgs => [...msgs, { role, text, timestamp: new Date() }]);
    this.shouldScroll = true;
  }
}
