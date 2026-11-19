-- Auto-generated from CustomerInfo.csv

-- Usage: psql -U dsoler -d Datanalytics -v ON_ERROR_STOP=1 -f SeedCustomerInfo.sql



SET enable_mergejoin = off;



-- Avacon (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Avacon')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398246560432', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Avacon')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'Avacon',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Avacon')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Westnetz (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Westnetz')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398249270000', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Westnetz')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'Westnetz',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Westnetz')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Syna (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Syna')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398248268726', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Syna')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'Syna',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Syna')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- NBB (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('NBB')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398247366692', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('NBB')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'NBB',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('NBB')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- EWE (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('EWE')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398251266011', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('EWE')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'EWE',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('EWE')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- ENBW (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('ENBW')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398247368526', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('ENBW')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'ENBW',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('ENBW')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Thuega Energienetze (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Thuega Energienetze')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398250189267', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Thuega Energienetze')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'Thuega Energienetze',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Thuega Energienetze')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Energieversorgung Filstal (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Energieversorgung Filstal')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398250462372', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Energieversorgung Filstal')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'Energieversorgung Filstal',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Energieversorgung Filstal')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- E-NETZ SUDHESSEN (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('E-NETZ SUDHESSEN')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398249781410', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('E-NETZ SUDHESSEN')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'E-NETZ SUDHESSEN',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('E-NETZ SUDHESSEN')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Netz Niederösterreich (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Netz Niederösterreich')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398256904676', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Netz Niederösterreich')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'Netz Niederösterreich',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Netz Niederösterreich')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Stedin (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Stedin')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '398260816518', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Stedin')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  6,
  6,
  20,
  NULL,
  'Stedin',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Stedin')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Gas Networks Ireland (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Gas Networks Ireland')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '385063165916', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Gas Networks Ireland')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  6,
  8,
  6,
  20,
  NULL,
  'Gas Networks Ireland',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Gas Networks Ireland')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Wales and West Utilities (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('Wales and West Utilities')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '390960004101', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Wales and West Utilities')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  6,
  8,
  6,
  20,
  NULL,
  'Wales and West Utilities',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('Wales and West Utilities')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;



-- Cadent (EU2)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU2'::text AS dblocation,
    false::boolean AS active
  FROM eu2."Customer" C
  WHERE lower(C."Name") = lower('Cadent')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '375691804502', NOW()
FROM eu2."Customer" C
WHERE lower(C."Name") = lower('Cadent')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  7,
  7,
  6,
  20,
  25,
  'Cadent',
  NOW()
FROM eu2."Customer" C
WHERE lower(C."Name") = lower('Cadent')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_POR" (
  customerid, "Year", startingdate, endingdate, description, "Value", unit, lastupdated
)
SELECT
  C."Id"::text,
  2026,
  '2026-04-01'::timestamp,
  '2027-03-31'::timestamp,
  'Cadent POR 2026',
  127000.0,
  'Km',
  NOW()
FROM eu2."Customer" C
WHERE lower(C."Name") = lower('Cadent')
ON CONFLICT (customerid, "Year") DO UPDATE SET
  startingdate = EXCLUDED.startingdate,
  endingdate = EXCLUDED.endingdate,
  description = EXCLUDED.description,
  "Value" = EXCLUDED."Value",
  unit = EXCLUDED.unit,
  lastupdated = EXCLUDED.lastupdated;



-- PSG (EU1)

WITH src AS (
  SELECT
    C."Id"::uuid AS customerid,
    C."Name" AS customer_name,
    'EU1'::text AS dblocation,
    true::boolean AS active
  FROM eu1."Customer" C
  WHERE lower(C."Name") = lower('PSG')
)
INSERT INTO kpihub."KPI_Customer" (
  customerid, "Name", shortname, active, dblocation, lastupdated
)
SELECT
  customerid,
  customer_name,
  regexp_replace(customer_name, '\s+', '', 'g'),
  active,
  dblocation,
  NOW()
FROM src
ON CONFLICT (customerid) DO UPDATE SET
  "Name" = EXCLUDED."Name",
  shortname = EXCLUDED.shortname,
  active = EXCLUDED.active,
  dblocation = EXCLUDED.dblocation,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_OutputExcelLocation" (customerid, boxfolderid, lastupdated)
SELECT C."Id"::uuid, '402825591696', NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('PSG')
ON CONFLICT (customerid) DO UPDATE SET
  boxfolderid = EXCLUDED.boxfolderid,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_Utilization" (
  customerid, workingdays, workinghours, sunrisehour, sunsethour,
  basesurveyorcount, description, lastupdated
)
SELECT
  C."Id"::uuid,
  5,
  8,
  6,
  20,
  NULL,
  'PSG',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('PSG')
ON CONFLICT (customerid) DO UPDATE SET
  workingdays = EXCLUDED.workingdays,
  workinghours = EXCLUDED.workinghours,
  basesurveyorcount = EXCLUDED.basesurveyorcount,
  description = EXCLUDED.description,
  lastupdated = EXCLUDED.lastupdated;

INSERT INTO kpihub."KPI_POR" (
  customerid, "Year", startingdate, endingdate, description, "Value", unit, lastupdated
)
SELECT
  C."Id"::text,
  2026,
  '2026-04-01'::timestamp,
  '2026-12-31'::timestamp,
  'PSG POR 2026',
  5300.0,
  'Km',
  NOW()
FROM eu1."Customer" C
WHERE lower(C."Name") = lower('PSG')
ON CONFLICT (customerid, "Year") DO UPDATE SET
  startingdate = EXCLUDED.startingdate,
  endingdate = EXCLUDED.endingdate,
  description = EXCLUDED.description,
  "Value" = EXCLUDED."Value",
  unit = EXCLUDED.unit,
  lastupdated = EXCLUDED.lastupdated;


