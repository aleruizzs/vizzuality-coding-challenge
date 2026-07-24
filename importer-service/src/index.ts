import express, { Request, Response } from 'express';
import multer from 'multer';
import { checkDbConnection } from './database';
import { config } from './config';
import { processCsvFile } from './importer';

const app = express();

const upload = multer({ dest: 'uploads/' });

app.use(express.json());

// Health check endpoint
app.get('/health', (_req: Request, res: Response) => {
  res.status(200).json({ status: 'ok', service: 'importer-service' });
});

// Endpoint to handle CSV file uploads
app.post('/upload', upload.single('file'), async (req: Request, res: Response) => {
  // Explicitly check if a file was uploaded under the key 'file'
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded under key "file"' });
  }

  try {
    const message = await processCsvFile(req.file.path);
    
    return res.status(200).json({
      message: 'File uploaded and processed successfully',
      details: message,
    });
  } catch (error) {
    console.error('Error processing CSV file:', error);
    return res.status(500).json({ error: 'Error processing CSV file' });
  }
});

app.listen(config.port, () => {
  console.log(`Importer service is running on port ${config.port}`);
  checkDbConnection();
});