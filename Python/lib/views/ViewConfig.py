WEEKLY_KPI_CUSTOMER ={
      "Name": "Weekly_KPI_Customer",
      "PeriodType": "Week",
      "Columns": {
"ReportAssetLengthKm": "float",
    "AssetCoveredLengthKm": "float",
    "DistributionPipeKm": "float",
    "DistributionPipeCoveredKm": "float",
    "CumulativeAssetCoveredLengthKm": "float",
    "ServicePipeKm": "float",
    "ServicePipeCoveredKm": "float",
    "ReportCount": "int",
    "DaysCount": "int",
    "FOVMain": "float",
    "SurveyDurationHours": "float",
    "TargetDurationHours": "float",
    "CustomerUtilization": "float",
    "StarndardUtilization": "float",
    "TotalSurveyors": "int",
    "ProductivityPerSurveyor": "float",
    "SurveyCount": "int",
    "AvgSpeedKm": "float",
    "SurveysCarDay": "float",
    "IdleTime": "float",
    "TotalDrivenLengthKm": "float",
    "DrivingRatio": "float",
    "NightDrivenLength": "float",
    "DayDrivenLength": "float",
    "NightRatio": "float",
    "DayRatio": "float",
    "PeakAboveSATCount": "int",
    "LisaCount": "int",
    "EmissionRate": "float",
    "B0Count": "int",
    "B1Count": "int",
    "Bm1Count": "int",
    "Bm2Count": "int",
    "NGCount": "int",
    "PGCount": "int",
    "Not_NGCount": "int",
    "LisaDensity": "float",
    "InstantanoeusEmission": "float",
    "B0Density": "float",
    "B1Density": "float",
    "Bm1Density": "float",
    "Bm2Density": "float",
    "B0Share": "float",
    "B1Share": "float",
    "Bm1Share": "float",
    "Bm2Share": "float",
    "NGShare": "float",
    "PGShare": "float",
    "Not_NGShare": "float",
    "POR": "float",
    "CurrentCompletion": "float",
      },
} 

YEARLY_KPI_CUSTOMER  = WEEKLY_KPI_CUSTOMER.copy()
YEARLY_KPI_CUSTOMER["PeriodType"] = "Year"
YEARLY_KPI_CUSTOMER["Name"] = "Yearly_KPI_Customer"

MONTHLY_KPI_CUSTOMER  = WEEKLY_KPI_CUSTOMER.copy()
MONTHLY_KPI_CUSTOMER["PeriodType"] = "Month"
MONTHLY_KPI_CUSTOMER["Name"] = "Monthly_KPI_Customer"

KPI_CUSTOMER_VIEWS = [WEEKLY_KPI_CUSTOMER, YEARLY_KPI_CUSTOMER, MONTHLY_KPI_CUSTOMER]