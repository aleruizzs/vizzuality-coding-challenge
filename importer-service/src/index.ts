import express, { Request, Response } from 'express';
import { checkDbConnection } from './database';
import { config } from './config';

const app = express();

app.use(express.json());

app.get('/health', (_req: Request, res: Response) => {
  res.status(200).json({ status: 'ok', service: 'importer-service' });
});

app.listen(config.port, () => {
  console.log(`Importer service is running on port ${config.port}`);
  checkDbConnection();
});