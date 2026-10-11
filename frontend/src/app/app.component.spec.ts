import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { AppComponent } from './app.component';
import { AuthStore } from './core/auth-store';

describe('AppComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [provideRouter([]), provideHttpClient()],
    }).compileComponents();
  });

  it('creates the app shell', () => {
    const fixture = TestBed.createComponent(AppComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows navigation only when connected', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const auth = TestBed.inject(AuthStore);
    auth.disconnect();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('nav a')).toBeNull();
    auth.connect('token', 'tenant-1');
    fixture.detectChanges();
    const links = [...fixture.nativeElement.querySelectorAll('nav a')].map((a: Element) => a.textContent);
    expect(links).toContain('Runs');
    expect(links).toContain('Approvals');
  });
});
