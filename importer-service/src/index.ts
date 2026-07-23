import express, { Request, Response } from 'express';

const app = express();

app.use(express.json());

app.get('/health', (_req: Request, res: Response) => {
  res.status(200).json({ status: 'ok', service: 'importer-service' });
});

app.listen(3000, () => {
  console.log('Importer service is running on port 3000');
});