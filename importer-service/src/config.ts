import dotenv from 'dotenv';

dotenv.config();

function requireEnv(key: string): string {
  const v = process.env[key];
  if (v === undefined || v === '') {
    throw new Error(`Environment variable ${key} is required`);
  }
  return v;
}

export const config = {
  port: Number(requireEnv('EXPRESS_PORT')),
  db: {
    host: requireEnv('POSTGRES_HOST'),
    port: Number(requireEnv('POSTGRES_PORT')),
    user: requireEnv('POSTGRES_USER'),
    pass: requireEnv('POSTGRES_PASSWORD'),
    name: requireEnv('POSTGRES_DB'),
  },
};