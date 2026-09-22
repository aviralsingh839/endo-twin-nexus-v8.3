"""Synthetic cases for the V8.6 workstation showcase. Never clinical records."""
from dataclasses import dataclass
from typing import List
@dataclass(frozen=True)
class DemoCase:
    patient:str; alias:str; age:int; bmi:float; condition:str; tier:str; risk:float; quality:float; hr:float; hrv:float; temp:float; activity:float; sleep:float; drivers:tuple[str,...]; last_seen:str
DEMO_CASES:List[DemoCase]=[
 DemoCase("Patient 021","Mira",23,24.7,"CHRONO-PCOS","High",78,0.94,88,31,32.7,24,6.1,("cycle irregularity","low HRV","repeated pattern"),"Today 23:07"),
 DemoCase("Patient 014","Anika",27,27.3,"CHRONO-PCOS","Elevated",64,0.91,82,36,32.6,31,6.7,("cycle variability","activity deviation"),"Today 22:51"),
 DemoCase("Patient 033","Ira",31,29.1,"Cardiometabolic pattern","Elevated",58,0.89,84,39,32.4,28,6.4,("activity context","longitudinal change"),"Today 22:13"),
 DemoCase("Patient 009","Rhea",22,22.8,"Autonomic pattern","Moderate",47,0.93,79,41,32.5,52,7.2,("HRV trend","recovery context"),"Today 21:44"),
 DemoCase("Patient 027","Tara",25,26.1,"Sleep pattern","Moderate",42,0.86,76,44,32.6,39,5.9,("sleep timing","sleep regularity"),"Today 20:38"),
 DemoCase("Patient 041","Noor",29,23.9,"CHRONO-PCOS","Low",23,0.97,71,50,32.5,61,7.6,("no persistent driver",),"Today 19:52"),
 DemoCase("Patient 018","Meera",34,25.2,"No active disease model","Unknown",0,0.88,74,47,32.5,56,7.1,("no model run",),"Yesterday"),
 DemoCase("Patient 052","Zoya",28,30.2,"CHRONO-PCOS","Elevated",69,0.82,91,29,32.8,22,6.0,("low HRV","cycle variability","data quality"),"Yesterday")]
ORDER={"High":4,"Elevated":3,"Moderate":2,"Low":1,"Unknown":0}
def condition_list(): return ["All conditions"]+sorted({x.condition for x in DEMO_CASES})
def sorted_cases(condition="All conditions",sort_key="priority"):
    rows=[x for x in DEMO_CASES if condition=="All conditions" or x.condition==condition]
    if sort_key=="condition": return sorted(rows,key=lambda x:(x.condition,-ORDER[x.tier],-x.risk,x.patient))
    if sort_key=="risk": return sorted(rows,key=lambda x:(-x.risk,-ORDER[x.tier],x.patient))
    return sorted(rows,key=lambda x:(-ORDER[x.tier],-x.risk,x.condition,x.patient))
