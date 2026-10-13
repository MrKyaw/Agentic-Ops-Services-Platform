import { TestBed } from '@angular/core/testing';
import { AuthStore } from './auth-store';

describe('AuthStore', () => {
  it('starts disconnected', () => {
    TestBed.configureTestingModule({});
    const auth = TestBed.inject(AuthStore);
    auth.disconnect();
    expect(auth.connected).toBeFalse();
  });

  it('connects and persists across instances', () => {
    TestBed.configureTestingModule({});
    const auth = TestBed.inject(AuthStore);
    auth.connect('tok', 'tenant-9');
    expect(auth.connected).toBeTrue();
    expect(auth.token()).toBe('tok');
    expect(auth.tenant()).toBe('tenant-9');
    expect(localStorage.getItem('sap.token')).toBe('tok');
  });

  it('disconnect clears state and storage', () => {
    TestBed.configureTestingModule({});
    const auth = TestBed.inject(AuthStore);
    auth.connect('tok', 'tenant-9');
    auth.disconnect();
    expect(auth.connected).toBeFalse();
    expect(localStorage.getItem('sap.token')).toBeNull();
  });
});
