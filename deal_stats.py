#/bin/env python3

import os, sys
from typing import *
import json
import pandas as pd
import matplotlib.pyplot as plt 
from tabulate import tabulate
import argparse

trigger_info : Dict = {
    "coupon": {
        "value": 0
    },
    "level": {
        "value": 99.99
    },
    "level_up": True
}

tarn : Dict = {
    "basic_tarn": {
        "type": "NONE"
    }
}

asian_tail : Dict = {
    "performance": {
        "type": "EUROPEAN"
    }
}

def process_file(filein: TextIO) -> Dict[str, float]:
    data: Dict = json.load(filein)
    output: Dict = dict(data)

    payload = output["payload"]
    payload["model"].pop("american_montecarlo_model")

    cancel_option = payload["product"].pop("callable")
    trigger_dates = cancel_option.pop("event_date")

    for event in trigger_dates:
        if "callable_info" in event:
            date = event["callable_info"]["funding_end_date"]
            event.pop("callable_info")

            event["cancel_trigger"] = {
                "cancel_date": date,
                "trigger_info": trigger_info
            }

    cancel_option["trigger_dates"] = trigger_dates
    cancel_option["type"] = "DOUBLETRIGGER"
    cancel_option["pay_at_fixings"] = True
    cancel_option["funding_legs"] = []
    cancel_option["cancel_cost_of_hedge"] = cancel_option["coupon_cost_of_hedge"]

    if "funding_leg" in cancel_option:
        leg = cancel_option.pop("funding_leg")
        if bool(leg): # not add empty [{}]
            cancel_option["funding_legs"].append(leg)

    cancel_option.pop("memory")
    final_payoff = cancel_option.pop("final_payoff")

    payload["product"]["autocall"] = {
        "cancel_option" : cancel_option,
        "memory" : {},
        "tarn" : tarn,
        "asian_tail" : asian_tail
    }
    payload["product"]["autocall"] |= final_payoff # == merge

    parameters = payload["simulation_parameters"]["monte_carlo_parameters_array"]["monte_carlo_parameters"]
    parameters = list(filter(lambda x : x["id"] != "AMERICAN_MONTECARLO", parameters))
    payload["simulation_parameters"]["monte_carlo_parameters_array"]["monte_carlo_parameters"] = parameters

    return output

if __name__ == "__main__":
    inprefix : str = os.path.dirname(os.path.commonprefix(sys.argv[1:]))
    outprefix : str = inprefix+"_nocal"
    os.mkdir(outprefix)

    for filename in sys.argv[1:]:
        if os.path.isfile(filename):
            print(f"Processing {filename}")
            transformed_json : Dict
            try:
                with open(filename) as fin:
                    transformed_json = process_file(fin)

                outfilename : str = filename.replace(inprefix, outprefix)
                with open(outfilename, "w") as fout:
                    print(f"Write output to {outfilename}")
                    json.dump(transformed_json, fout, indent=4)

            except IOError:
                print(f"Couldn't open input:{fname_in}", file = sys.stderr)
        else:
            print(f"Path: '{filename}' is not a file", file = sys.stderr)
