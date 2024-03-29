class MCStatType:
    Nminutes_per_job = 0
    Nions_per_beam = 1
    Xpct_unc_in_target = 2
    NTypes = 3
    default_values = [0,int(5e7),0.0] # everything off: user should give a postive value to at least one
    unit = ("min/job","ions/beam","%")
    guilabels = ("N minutes per job","N ions/beam", "X %unc in target")
    cfglabels = ("n minutes per job","n ions per beam","x pct unc in target")
    is_int = (True,True,False)

class MCPriorityType:
    Low = 0
    Normal = 1
    High = 2
    NTypes = 3
    labels = ("Low", "Normal", "High")
    condor_priorities = (0,10,20)

