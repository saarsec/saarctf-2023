import { TestBed } from '@angular/core/testing';

import { RedisBackendService } from './redis-backend.service';

describe('RedisBackendService', () => {
  let service: RedisBackendService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(RedisBackendService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
