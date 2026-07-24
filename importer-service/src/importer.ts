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
    let rowsToInsert: EmissionRow[] = [];
    let totalInserted = 0;
    let skippedRows = 0;
    let minVal: number | null = null;
    let maxVal: number | null = null;

    try {
        const stream = fs.createReadStream(filePath).pipe(csv());

        // Read the CSV file and parse each row
        for await (const row of stream) {
            // Extract the country, sector, and parent sector from the row
            const country = row[COUNTRY_COLUMN]?.trim();
            const sector = row[SECTOR_COLUMN]?.trim();
            const parentSector = row[PARENT_SECTOR_COLUMN]?.trim() || null;

            // Skip rows that don't have a valid country or sector, since these are mandatory fields
            if (!country || !sector) {
                skippedRows++;
                continue;
            }

            // Iterate over the keys of the row to find year columns and their corresponding values
            for (const year of Object.keys(row)) {
                if (year !== COUNTRY_COLUMN && year !== SECTOR_COLUMN && year !== PARENT_SECTOR_COLUMN) {
                    // Ensure the year is a valid number before processing
                    const yearNum = parseInt(year?.trim(), 10);
                    if (!isNaN(yearNum)) {
                        const rawValue = row[year]?.trim();
                        const parsedValue = parseFloat(rawValue);

                        // If the value is not a valid number, set it to null
                        const value = rawValue !== undefined && rawValue !== '' && !isNaN(parsedValue) 
                        ? parsedValue
                        : null;

                        // Update min and max values
                        if (value !== null) {
                            if (minVal === null || value < minVal)  minVal = value;
                            if (maxVal === null || value > maxVal) maxVal = value;
                        }
                        // If this row has a valid year but the value is invalid, we skip it and increment the skippedRows counter
                        else {
                            skippedRows++;
                            continue;
                        }

                        rowsToInsert.push({
                            country,
                            sector,
                            parentSector,
                            year: yearNum,
                            value,
                        });
                    }
                }
            }

            // If the number of rows to insert reaches the batch size, pause the stream to process the current batch
            if (rowsToInsert.length >= BATCH_SIZE){
                // Free up memory by inserting the current batch into the database
                const batch = rowsToInsert;
                rowsToInsert = [];

                await db.insert(emissions).values(batch).execute();
                totalInserted += batch.length;
                }
        }

        // Insert any remaining rows that didn't fill a complete batch
        if (rowsToInsert.length > 0) {
            await db.insert(emissions).values(rowsToInsert).execute();
            totalInserted += rowsToInsert.length;
        }

        return{
            message: 'CSV file data saved successfully.',
            summary: {
                totalRecords: totalInserted,
                skippedRows: skippedRows,
                minEmissions: minVal,
                maxEmissions: maxVal,
            },
        };
    } finally {
        // Clean up the uploaded file after processing, regardless of success or failure
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
    }
}