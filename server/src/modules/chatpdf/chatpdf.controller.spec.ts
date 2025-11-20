import { Test, TestingModule } from '@nestjs/testing';
import { ChatpdfController } from './chatpdf.controller';

describe('ChatpdfController', () => {
  let controller: ChatpdfController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [ChatpdfController],
    }).compile();

    controller = module.get<ChatpdfController>(ChatpdfController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});
