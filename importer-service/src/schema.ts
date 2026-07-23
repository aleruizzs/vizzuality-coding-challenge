import { pgTable, serial, varchar, integer, doublePrecision, index } from 'drizzle-orm/pg-core';

export const emissions = pgTable('emissions', {
    id: serial('id').primaryKey(),
    country: varchar('country', { length: 255 }).notNull(),
    sector: varchar('sector', { length: 255 }).notNull(),
    parentSector: varchar('parent_sector', { length: 255 }),
    year: integer('year').notNull(),
    value: doublePrecision('value'),
}, (table) => [
    index('idx_emissions_country').on(table.country),
    index('idx_emissions_sector').on(table.sector),
    index('idx_emissions_parent_sector').on(table.parentSector),
]);