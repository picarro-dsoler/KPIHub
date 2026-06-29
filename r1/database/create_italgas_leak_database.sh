#! /bin/bash

# save my current directory
MY_CWD=$(pwd)

cd ..

# change to database directory
cd database || exit


#----Client Tables
#ClientName
#Region = EU1, EU2, US1, Custom
#ClientId

#----BreadCrumb Table
#SurveyId
#BreadCrumbCount

#---- KPI_Definition Table
#IId : UUID PRIMARY KEY
#KPIName : VARCHAR(255) 
#KPIDescription : TEXT
#KPIType : VARCHAR(255)
#KPIValueTimestamp : TIMESTAMP

#----KPI Tables
#The tables will be created as:
# Monthly_KPI
# Daily_KPI
# Yearly_KPI
# Quarterly_KPI

#Columns of the KPI Table:
#ID : INTEGER PRIMARY KEY AUTOINCREMENT
#KPIId : UUID
#KPIDefinitionId : UUID 
#Label : VARCHAR(255)
#Value : FLOAT
#LastUpdated : TIMESTAMP


# Indexes will be assigned as (For the KPIId)
# For Yearly_KPI:
# ClientName_Y2026

# For Monthly_KPI:
# ClientName_Y2026_M1

# For Daily_KPI:
# CllentName_Y2026_D1    #D1 is the first day of the year

# For Weekly_KPI:
# ClientName-Y2026-W1

# For Quarterly_KPI:
# ClientName-Y2026-Q1


sqlite3 picarro_kpi.db "create table Leaks (
leakId INTEGER PRIMARY KEY,
numProgressivo INTEGER,
lisa TEXT,
aereoInterrato TEXT,
codiceDispersione TEXT,
codStato TEXT,
xCoord REAL,
yCoord REAL,
statoFoglietta TEXT,
codValidazione TEXT,
statoValidazione TEXT,
intervento TEXT,
dataInserimento INTEGER,
dataArrivoSulCampo INTEGER,
dataLocalizzazione INTEGER,
dataRiparazione INTEGER,
cap TEXT,
comune TEXT,
indirizzo TEXT,
indirizzoLisa TEXT,
indirizzoLocalizzazione TEXT,
indirizzoRiparazione TEXT,
accertamentoRiscontrato TEXT,
descrizioneAsset TEXT,
sedeTecnicaLocalizzata TEXT,
dataUltimaMod INTEGER,
picarroLastUpdated INTEGER,
idAzienda INTEGER
);"

# change directory back to the original
cd $MY_CWD || exit


exit
