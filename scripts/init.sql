CREATE TABLE IF NOT EXISTS emissions (
    id SERIAL PRIMARY KEY,
    country VARCHAR(255) NOT NULL,
    sector VARCHAR(255) NOT NULL,
    parent_sector VARCHAR(255),
    year INT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    CONSTRAINT unique_country_sector_year UNIQUE NULLS NOT DISTINCT (country, sector, parent_sector, year)
);

CREATE INDEX IF NOT EXISTS idx_emissions_country ON emissions(country);
CREATE INDEX IF NOT EXISTS idx_emissions_sector ON emissions(sector);
CREATE INDEX IF NOT EXISTS idx_emissions_parent_sector ON emissions(parent_sector);
CREATE INDEX IF NOT EXISTS idx_emissions_year ON emissions(year);