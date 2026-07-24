import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import fs from 'fs';
import path from 'path';
import { processCsvFile } from '../src/importer';


// Mock the database functions to avoid actual database operations during tests
const { mockInsert, mockValues } = vi.hoisted(() => {
    const mockExecute = vi.fn().mockResolvedValue(true);
    const mockValues = vi.fn().mockReturnValue({ execute: mockExecute });
    const mockInsert = vi.fn().mockReturnValue({ values: mockValues });
    return { mockInsert, mockValues };
});

// Mock the database module to replace the actual database operations with our mocks
vi.mock('../src/database', () => ({
    db: { insert: mockInsert },
}));


// Test suite for the processCsvFile function
describe('processCsvFile', () => {
    const testDir = path.join(__dirname, 'temp_csv_tests');

    // Create a temporary directory for test CSV files before each test and reset mocks
    beforeEach(() => {
        if (!fs.existsSync(testDir)) {
            fs.mkdirSync(testDir, { recursive: true });
        }
        vi.clearAllMocks();
        
        mockInsert.mockReturnValue({ values: mockValues });
        mockValues.mockReturnValue({ execute: vi.fn().mockResolvedValue(true) });
  });

    // Clean up the temporary directory after all tests
    afterAll(() => {
        if (fs.existsSync(testDir)) {
            fs.rmSync(testDir, { recursive: true });
        }
    });

    it('Returns the expected structure', async () => {
        const csvPath = path.join(testDir, 'returns_expected_structure.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990\nSpain,Transport,Transport,10.5\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result).toHaveProperty('message');
        expect(result).toHaveProperty('summary');
        expect(result.summary).toHaveProperty('totalRecords');
        expect(result.summary).toHaveProperty('skippedRows');
        expect(result.summary).toHaveProperty('minEmissions');
        expect(result.summary).toHaveProperty('maxEmissions');
    });

    it('Processes multiple rows and years correctly', async () => {
        const csvPath = path.join(testDir, 'multiple_rows.csv');
        fs.writeFileSync(csvPath, 
            'Country,Sector,Parent Sector,1990,1991,1992\n' +
            'Spain,Transport,Transport,1,2,3\n' +
            'France,Agriculture,Agriculture,4,5,6\n'
        );
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.totalRecords).toBe(6);
    });

    it('Inserts the exact mapped objects into the database', async () => {
        const csvPath = path.join(testDir, 'db_payload.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990\nSpain,Transport,Energy,10.5\n');

        await processCsvFile(csvPath);

        expect(mockValues).toHaveBeenCalledWith([
        {
            country: 'Spain',
            sector: 'Transport',
            parentSector: 'Energy',
            year: 1990,
            value: 10.5,
        },
        ]);
    });

    it('Null country values are skipped', async () => {
        const csvPath = path.join(testDir, 'null_country.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990,1991\n,,Transport,Transport,10.5,20.0\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.totalRecords).toBe(0);
        expect(result.summary.skippedRows).toBe(1);
    });

    it('Null sector values are skipped', async () => {
        const csvPath = path.join(testDir, 'null_sector.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990,1991\nSpain,,Transport,10.5,20.0\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.totalRecords).toBe(0);
        expect(result.summary.skippedRows).toBe(1);
    });

    it('Allows empty Parent Sector (null)', async () => {
        const csvPath = path.join(testDir, 'allows_empty_parent_sector.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990\nSpain,Transport,,10.5\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.totalRecords).toBe(1);
    });

    it('Values are trimmed', async () => {
        const csvPath = path.join(testDir, 'trimmed_values.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990,1991\n Spain , Transport , Transport , 10.5 ,    20.0 \n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.totalRecords).toBe(2);
        expect(mockValues).toHaveBeenCalledWith([
            {
                country: 'Spain',
                sector: 'Transport',
                parentSector: 'Transport',
                year: 1990,
                value: 10.5,
            },
            {
                country: 'Spain',
                sector: 'Transport',
                parentSector: 'Transport',
                year: 1991,
                value: 20.0,
            }
        ]);
    });

    it('Years are parsed correctly', async () => {
        const csvPath = path.join(testDir, 'years_parsing.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990,1991\nSpain,Transport,Transport,10.5,20.0\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.totalRecords).toBe(2);
    });

    it('Ignores non-year columns', async () => {
        const csvPath = path.join(testDir, 'non_year_columns.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990,InvalidYear\nSpain,Transport,Transport,10.5,abc\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.totalRecords).toBe(1);
    });

    it('Handles null year values correctly', async () => {
        const csvPath = path.join(testDir, 'null_values.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990\nSpain,Transport,Transport,\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.minEmissions).toBeNull();
        expect(result.summary.maxEmissions).toBeNull();
        expect(result.summary.totalRecords).toBe(0);
        expect(result.summary.skippedRows).toBe(1);
    });

    it('Handles null values correctly for different values', async () => {
        const csvPath = path.join(testDir, 'null_values_different.csv');
        fs.writeFileSync(
            csvPath,
            'Country,Sector,Parent Sector,1990,1991\n' +
            'Spain,Transport,Transport,,,\n' +
            'France,Agriculture,Agriculture,1,2,\n'
        );
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.totalRecords).toBe(2);
        expect(result.summary.skippedRows).toBe(2);
    });

    it('Handles wrong year values correctly', async () => {
        const csvPath = path.join(testDir, 'wrong_values.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990\nSpain,Transport,Transport,abc\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.minEmissions).toBeNull();
        expect(result.summary.maxEmissions).toBeNull();
    });

    it('Calculates minEmissions and maxEmissions correctly', async () => {
        const csvPath = path.join(testDir, 'min_max_emissions.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990,1991\nSpain,Transport,Transport,5.0,25.0\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.minEmissions).toBe(5.0);
        expect(result.summary.maxEmissions).toBe(25.0);
    });

    it('Preserves zero values correctly', async () => {
        const csvPath = path.join(testDir, 'zero_values.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990\nSpain,Transport,Transport,0\n');
        
        const result = await processCsvFile(csvPath);
        
        expect(result.summary.minEmissions).toBe(0);
        expect(result.summary.maxEmissions).toBe(0);
    });

    it('Handles negative emission values correctly for min/max', async () => {
        const csvPath = path.join(testDir, 'negative_values.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990,1991\nSpain,Transport,Transport,-10.5,-50.0\n');

        const result = await processCsvFile(csvPath);

        expect(result.summary.minEmissions).toBe(-50.0);
        expect(result.summary.maxEmissions).toBe(-10.5);
    });

    it('Executes database inserts in batches of 1000 records', async () => {
        const csvPath = path.join(testDir, 'batch_test.csv');
        
        const yearsHeader = Array.from({ length: 5 }, (_, i) => 2000 + i).join(',');
        let content = `Country,Sector,Parent Sector,${yearsHeader}\n`;
        for (let i = 0; i < 240; i++) {
            content += `Country${i},Sector${i},Parent Sector${i},10,20,30,40,50\n`;
        }
        fs.writeFileSync(csvPath, content);

        const result = await processCsvFile(csvPath);

        expect(result.summary.totalRecords).toBe(1200);
        expect(mockInsert).toHaveBeenCalledTimes(2);
    });

    it('Deletes the CSV file after finishing', async () => {
        const csvPath = path.join(testDir, 'ends_deletes.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990\nSpain,Transport,Transport,10.5\n');

        await processCsvFile(csvPath);

        expect(fs.existsSync(csvPath)).toBe(false);
    });

    it('Deletes the CSV file when there is an error', async () => {
        mockInsert.mockImplementationOnce(() => {
            throw new Error('Database connection lost');
        });

        const csvPath = path.join(testDir, 'fails_and_deletes.csv');
        fs.writeFileSync(csvPath, 'Country,Sector,Parent Sector,1990\nSpain,Transport,Transport,10.5\n');

        await expect(processCsvFile(csvPath)).rejects.toThrow('Database connection lost');

        expect(fs.existsSync(csvPath)).toBe(false);
    });

});