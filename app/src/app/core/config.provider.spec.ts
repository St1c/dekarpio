import { TestBed } from '@angular/core/testing';

import { ConfigProvider } from './config.provider';

describe('ConfigProvider', () => {
  let service: ConfigProvider;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ConfigProvider);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
