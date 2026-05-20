import pandas as pd
DIGITS = 2
def process_kpi(kpi_data):
    out_kpi = pd.DataFrame()
    out_kpi["AssetPercentCoverage"] = 100*((kpi_data["AssetCoveredLengthKm"]/kpi_data["ReportAssetLengthKm"]).apply(lambda x: round(x, 4)))
    out_kpi["ReportAssetLengthKm"] = kpi_data["ReportAssetLengthKm"].apply(lambda x: round(x, DIGITS))
    out_kpi["AssetCoveredLengthKm"] = kpi_data["AssetCoveredLengthKm"].apply(lambda x: round(x, DIGITS))

    out_kpi["InstatanoeusEmission"] = (kpi_data["EmissionRate"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))
    out_kpi["LisaDensity"] = (kpi_data["LisaCount"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))
    out_kpi["DrivingRatio"] = (kpi_data["DrivingLengthKM"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))

    out_kpi["B0 Density"] = (kpi_data["B0Count"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))
    out_kpi["B1 Density"] = (kpi_data["B1Count"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))
    out_kpi["B-1 Density"] = (kpi_data["Bm1Count"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))
    out_kpi["B-2 Density"] = (kpi_data["Bm2Count"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))
    out_kpi["NG Density"] = (kpi_data["NGCount"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))
    out_kpi["PG Density"] = (kpi_data["PGCount"] / kpi_data["AssetCoveredLengthKm"]).apply(lambda x: round(x, DIGITS))

    out_kpi["B0Share"] = (100 *  kpi_data["B0Count"] / kpi_data["LisaCount"]).apply(lambda x: round(x, DIGITS))
    out_kpi["B1Share"] = (100 * kpi_data["B1Count"] / kpi_data["LisaCount"]).apply(lambda x: round(x, DIGITS))
    out_kpi["B-1Share"] = (100 * kpi_data["Bm1Count"] / kpi_data["LisaCount"]).apply(lambda x: round(x, DIGITS))
    out_kpi["B-2Share"] = (100 * kpi_data["Bm2Count"] / kpi_data["LisaCount"]).apply(lambda x: round(x, DIGITS))
    out_kpi["NGShare"] = (100 * kpi_data["NGCount"] / kpi_data["LisaCount"]).apply(lambda x: round(x, DIGITS))
    out_kpi["PGShare"] = (100 * kpi_data["PGCount"] / kpi_data["LisaCount"]).apply(lambda x: round(x, DIGITS))

    out_kpi['IdleTime'] = (100 * (kpi_data['IdleTime']) / kpi_data['SurveyTime']).apply(lambda x: round(x, DIGITS))
    return out_kpi