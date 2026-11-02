-- What an app needs to run (docs/specs/apps.md, 3.1 and 4.7): who its calls run as (the viewer, or the app itself),
-- the CLIs its functions use, the secret names its manifest declares, and those not set on the rrotor when it last
-- said. Names only, never a value.
ALTER TABLE apps ADD COLUMN IF NOT EXISTS run_as TEXT DEFAULT 'viewer' NOT NULL;
ALTER TABLE apps ADD CONSTRAINT apps_run_as CHECK (run_as IN ('viewer', 'app'));
ALTER TABLE apps ADD COLUMN IF NOT EXISTS clis TEXT[] DEFAULT '{}'::text[] NOT NULL;
ALTER TABLE apps ADD COLUMN IF NOT EXISTS secrets TEXT[] DEFAULT '{}'::text[] NOT NULL;
ALTER TABLE apps ADD COLUMN IF NOT EXISTS secrets_missing TEXT[] DEFAULT '{}'::text[] NOT NULL;
