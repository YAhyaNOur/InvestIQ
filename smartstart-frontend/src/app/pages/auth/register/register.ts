import { apiErrorMessage } from '../../../core/utils/api-error';
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { Router } from '@angular/router';
import { finalize } from 'rxjs/operators';

type Role = 'STARTUPER' | 'INVESTOR';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './register.html',
  styleUrls: ['./register.css'],
})
export class Register implements OnInit {
  form!: FormGroup;
  loading = false;
  serverError = '';
  showPassword = false;
  successMessage = '';
  redirectTimeout: any;

  readonly roles: { value: Role; label: string; description: string; icon: string }[] = [
    { value: 'STARTUPER', label: 'Dirigeant / CEO', description: 'Je pilote mon entreprise, recrute et recherche des investisseurs', icon: 'startuper' },
    { value: 'INVESTOR', label: 'Investisseur', description: 'Je découvre, analyse et finance des projets innovants', icon: 'investor' },
  ];

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.form = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3), Validators.pattern(/^[a-zA-Z0-9_]+$/)]],
      email: ['', [Validators.required, Validators.email]],
      full_name: [''],
      password: ['', [Validators.required, strongPassword]],
      role: ['STARTUPER', Validators.required],
    });
  }

  selectRole(role: Role): void {
    this.form.patchValue({ role });
  }

  getFieldError(field: string): string {
    const control = this.form.get(field);
    if (!control || !control.invalid || !control.touched) return '';
    const errors = control.errors;
    if (errors?.['required']) return 'Ce champ est obligatoire';
    if (errors?.['email']) return 'Adresse email invalide';
    if (errors?.['minlength']) return `Minimum ${errors['minlength'].requiredLength} caractères`;
    if (errors?.['pattern']) {
      if (field === 'username') return 'Lettres, chiffres et underscore uniquement';
      return 'Format invalide';
    }
    if (errors?.['weakPassword']) return errors['weakPassword'];
    return '';
  }

  onSubmit(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid) return;

    this.loading = true;
    this.serverError = '';

    this.authService.register(this.form.value)
      .pipe(finalize(() => this.loading = false))
      .subscribe({
        next: (tokens) => {
          this.authService.saveTokens(tokens);
          const role = this.form.value.role as Role;
          this.successMessage = 'Compte créé avec succès ! Redirection...';

          this.redirectTimeout = setTimeout(() => {
            if (role === 'INVESTOR') {
              this.router.navigate(['/investor/onboarding']);
            } else {
              this.router.navigate(['/startuper/onboarding']);
            }
          }, 1500);
        },
        error: (err) => {
          this.serverError = apiErrorMessage(err);
        },
      });
  }
}

// Validateur personnalisé
function strongPassword(control: AbstractControl): ValidationErrors | null {
  const value = control.value || '';
  const hasMinLength = value.length >= 8;
  const hasUpperCase = /[A-Z]/.test(value);
  const hasNumber = /\d/.test(value);
  return hasMinLength && hasUpperCase && hasNumber ? null : { weakPassword: '8+ caractères, 1 majuscule, 1 chiffre' };
}