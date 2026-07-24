import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import request from 'supertest';
import { app } from '../src/index';
import { processCsvFile } from '../src/importer';
import fs from 'fs';
import path from 'path';

// Mock the config module to provide a fixed port for testing
vi.mock('../src/config', () => ({
    config: {
        port: 3000,
    },
}));

// Mock the processCsvFile function to avoid actual file processing during tests
vi.mock('../src/importer', () => ({
    processCsvFile: vi.fn(),
}));

// Mock the checkDbConnection function to avoid actual database connection checks during tests
vi.mock('../src/database', () => ({
    checkDbConnection: vi.fn(),
}));

// Test suite for the HTTP endpoints of the importer service
describe('HTTP Endpoints', () => {
    // Clear all mocks before each test to ensure a clean state
    beforeEach(() => {
        vi.clearAllMocks();
    });

    // Clean up the temporary directory after all tests end
    afterAll(() => {
        const testDir = path.join(__dirname, '../uploads');
        if (fs.existsSync(testDir)) {
            fs.rmSync(testDir, { recursive: true });
        }
    });

    describe('GET /health', () => {
        it('Returns status 200', async () => {
            const response = await request(app).get('/health');

            expect(response.status).toBe(200);
            expect(response.body).toEqual({
                status: 'ok',
                service: 'importer-service',
            });
        });
    });

    describe('POST /upload', () => {
        it('Returns HTTP 400 if no file is uploaded', async () => {
            const response = await request(app).post('/upload');

            expect(response.status).toBe(400);
            expect(response.body).toHaveProperty(
                'error',
                'No file uploaded under key "file"'
            );
            expect(processCsvFile).not.toHaveBeenCalled();
        });

        it('Returns HTTP 200 on successful file upload', async () => {
            const mockResult = {
                message: 'CSV file data saved successfully.',
                summary: {
                    totalRecords: 5,
                    skippedRows: 0,
                    minEmissions: 10.5,
                    maxEmissions: 50.0,
                },
            };

            vi.mocked(processCsvFile).mockResolvedValueOnce(mockResult as any);

            const response = await request(app)
                .post('/upload')
                .attach('file', Buffer.from('Country,Sector,Parent Sector,1990\nSpain,Energy,,10'), 'test.csv');

            expect(response.status).toBe(200);
            expect(response.body).toEqual({
                message: 'File uploaded and processed successfully',
                details: mockResult,
            });
            expect(processCsvFile).toHaveBeenCalledTimes(1);
        });

        it('Returns HTTP 500 when there is an error', async () => {
            vi.mocked(processCsvFile).mockRejectedValueOnce(new Error('Corrupted CSV file'));

            const response = await request(app)
                .post('/upload')
                .attach('file', Buffer.from('invalid,csv,data'), 'corrupted.csv');

            expect(response.status).toBe(500);
            expect(response.body).toHaveProperty('error', 'Error processing CSV file');
            expect(processCsvFile).toHaveBeenCalledTimes(1);
        });
    });
});