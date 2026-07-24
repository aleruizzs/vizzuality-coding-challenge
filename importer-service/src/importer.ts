import csv from 'csv-parser';
import fs from 'fs';
import { db } from './database';
import { emissions } from './schema';

// Basic interface for an emission row
interface EmissionRow {
  country: string;
  sector: string;
  parentSector: string | null;
  year: number;
  value: number | null;
}

const COUNTRY_COLUMN = 'Country', SECTOR_COLUMN = 'Sector', PARENT_SECTOR_COLUMN = 'Parent Sector';
const BATCH_SIZE = 1000;

export async function processCsvFile(filePath: string){
    const rowsToInsert: EmissionRow[] = [];

    return new Promise((resolve, reject) => {
        // Read the CSV file and parse each row
        fs.createReadStream(filePath)
            .pipe(csv())
            .on('data', (row) => {
                // Extract the country, sector, and parent sector from the row
                const country = row[COUNTRY_COLUMN];
                const sector = row[SECTOR_COLUMN];
                const parentSector = row[PARENT_SECTOR_COLUMN] || null;

                // Iterate over the keys of the row to find year columns and their corresponding values
                for (const year of Object.keys(row)) {
                    if (year !== COUNTRY_COLUMN && year !== SECTOR_COLUMN && year !== PARENT_SECTOR_COLUMN) {
                        // Ensure the year is a valid number before processing
                        if (!isNaN(parseInt(year, 10))) {
                            const rawValue = row[year];
                            const parsedValue = parseFloat(rawValue);

                            // If the value is not a valid number, set it to null
                            const value = rawValue !== undefined && rawValue !== '' && !isNaN(parsedValue) 
                            ? parsedValue
                            : null;
                            rowsToInsert.push({
                                country,
                                sector,
                                parentSector,
                                year: parseInt(year, 10),
                                value,
                            });
                        }
                    }
                }
            })
            .on('end', async () => {
                // Insert rows in batches
                let totalInserted = 0;
                for (let i = 0; i < rowsToInsert.length; i += BATCH_SIZE) {
                    const batch = rowsToInsert.slice(i, i + BATCH_SIZE);
                    await db.insert(emissions).values(batch).execute();
                    totalInserted += batch.length;
                }

                // Delete the file after processing
                if (fs.existsSync(filePath)) {
                    fs.unlinkSync(filePath);
                }

                resolve({ message: `CSV file data saved successfully. Total rows inserted: ${totalInserted}` });
            })
            .on('error', (error) => {
                // Delete the file if there's an error during processing
                if (fs.existsSync(filePath)) {
                    fs.unlinkSync(filePath);
                }
                reject(error);
            });
    });
}