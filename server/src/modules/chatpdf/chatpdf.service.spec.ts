import { Test, TestingModule } from '@nestjs/testing';
import { ChatpdfService } from './chatpdf.service';

describe('ChatpdfService', () => {
  let service: ChatpdfService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [ChatpdfService],
    }).compile();

    service = module.get<ChatpdfService>(ChatpdfService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
