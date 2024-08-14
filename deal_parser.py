#/bin/env python3

import os, sys
from typing import Dict, TextIO, Pattern, TypeAlias
import json
from tabulate import tabulate
import pandas as pd
from numbers import Number
import re
import numpy as np
import matplotlib.pyplot as plt

TIME_UNITS: Dict[str,float] = {"us": 1.E-6, "ms": 1.E-3, "s": 1, "m": 60, "h": 3600, "d": 86400}

re_result: Pattern[str] = re.compile(r"\S+//?(\S*?)_result(?:_\d+)?\.json")
re_external: Pattern[str] = re.compile(r"# Command:.*?-o " + re_result.pattern + r".*?Total execution time: (\S+s)", re.DOTALL)


def translateStrToTime(pvalue : str) -> float:
    matches = re.match(r"([\d\.]+)(us|ms|s|m|h|d)", pvalue)
    if not matches:
        raise Exception(f"String {pvalue} is not convertible to time unit")

    unit = matches.group(2)
    if unit not in TIME_UNITS:
        raise Exception(f"String {unit} is not a valid unit: {list(TIME_UNITS.keys())}")

    return float(matches.group(1)) * TIME_UNITS[matches.group(2)]

def processEntry(entry: Dict) -> float | int:
    assert len(entry) == 1

    ptype = list(entry.keys())[0]
    pvalue = entry[ptype]

    if ptype == 'duration_value':
        return translateStrToTime(pvalue)
    elif ptype == 'int64_value':
        return int(pvalue)

    raise Exception(f"Sorry, type:{ptype} is not supported.")
    return None

def processAttributes(attr : Dict) -> float | int:
    return processEntry(attr['duration_avg'])
    ret = {}
    ret["duration"] = processEntry(attr['duration_avg'])
    ret["request"] = processEntry(attr["request_payload_size_total"])
    ret["response"] = processEntry(attr["response_payload_size_total"])
    return ret

def getAttrValue(arr, *argv) -> Dict | list | float:
    arrIt = arr
    for key in argv:
        if isinstance(arrIt, dict):
            if key not in arrIt:
                raise Exception(f"Sorry, no key:{key} in dict.")
            arrIt = arrIt[key]

        elif isinstance(arrIt, list):
            for entry in arrIt:
                if entry["name"] == key:
                    arrIt = entry
                    break
            else:
                raise Exception(f"Sorry, no entry with name:{key} in list.")
        else:
            raise Exception(f"Entry is an invalid type: {type(arrIt)}.")

        if key == "attributes":
            return processAttributes(arrIt)

        if (type(arrIt) is str) and arrIt.endswith(tuple(TIME_UNITS.keys())):
            return translateStrToTime(arrIt)

    return arrIt;

def process_file(jsondata: Dict) -> Dict[str, float] | None:
    result: Dict = {}

    # Check first the status code
    status_code: str = getAttrValue(jsondata, "status", "code")
    if (status_code != 'OK'):
        print(f"Output failed with code: {status_code}", file = sys.stderr)
        return

    # base is a sort of shortcut reference. It will be moved to simplify latter
    # also shorter path implies a more efficient getAttrValue
    base = getAttrValue(jsondata, "time_record", "children", "Valuate", "children")
    assert base
    # These fields are only in callable outputs
    if any(x["name"] == "CallableSampling" for x in base):
        result["Sampling"] = getAttrValue(base, "CallableSampling", "span", "duration")

        result["SamplingLV"] = getAttrValue(base, "CallableSampling", "children", "LOCAL_VOL_VALUATION", "span", "duration")
        result["SamplingHV"] = getAttrValue(base, "CallableSampling", "children", "HESTON_VOL_VALUATION", "span", "duration")
        result["SamplingSV"] = getAttrValue(base, "CallableSampling", "children", "LOCAL_STOCH_VOL_VALUATION", "span", "duration")

        result["Regressors"] = getAttrValue(base, "Regressors", "span", "duration")

    # Move reference
    base = getAttrValue(base, "HestonTotal")
    result["HestonTotal"] = getAttrValue(base, "span", "duration")

    result["HestonLV"] = getAttrValue(base, "children", "LOCAL_VOL_VALUATION", "span", "duration")

    # Move reference
    base = getAttrValue(base, "children", "HestonCorr", "children", "Valuate", "children", "HestonCorr", "children")

    result["HestonV"] = getAttrValue(base, "HESTON_VOL_VALUATION",  "span", "duration")
    result["HestonSV"] = getAttrValue(base, "LOCAL_STOCH_VOL_VALUATION", "span", "duration")

    result["Total Internal"] = getAttrValue(jsondata, "time_record", "span", "duration")

    return result

class MyDict(dict):

    def __init__(self, arg1: Dict[str, float] | None = None):
        if (arg1):
            self.appendDict(arg1)

    def appendDict(self, arg1: Dict[str, float]) -> None:
        for key, value in arg1.items():
            self.appendValue(key, value)

    def appendValue(self, key: str, value: float) -> None:
        if key not in self:
            super().__setitem__(key, [value])
        else:
            super().__getitem__(key).append(value)

    def __setitem__(self, key: str, value: list[float]) -> None:
        assert key not in self
        super().__setitem__(key, value)

    def getmeans(self) -> Dict[str, float]:
        return {subkey: np.mean(sublist) for subkey, sublist in self.items()}

    @staticmethod
    def parseLogFile(logfile: TextIO):
        """Parse the logfile to get the user times"""
        content: str = logfile.read()
        matches = re.findall(re_external, content)

        user_times = MyDict()
        for match in matches:
            print(match)
            user_times.appendValue(match[0], translateStrToTime(match[1]))

        return user_times

Container: TypeAlias = Dict[str, MyDict]

class MyTable(dict):
    @staticmethod
    def processMultiple(jsonfiles: list[str], logfilename: str) -> Container:
        result: Container = {}

        # read the json_result files
        for filename in jsonfiles:
            if os.path.isfile(filename):
                matches = re.match(re_result, filename)
                if not matches:
                    print(f"Filename:{filename} does not match regex", file = sys.stderr)
                    continue
                key: str = matches.group(1)
                print(f"Processing {filename} -> {key}")
                try:
                    with open(filename) as fin:
                        jsondata: Dict = json.load(fin)
                        datai: Dict[str, float] | None = process_file(jsondata)
                        if key not in result:
                            print(f"Adding new key: {key}")
                            result[key] = MyDict()

                        if not datai:
                            print(f"Output file {filename} failed", file = sys.stderr)
                            continue

                        result[key].appendDict(datai)
                except IOError:
                    print(f"Couldn't open input:{filename}", file = sys.stderr)
            else:
                print(f"Path: '{filename}' is not a file", file = sys.stderr)

        # Readlog to get the user times
        if os.path.isfile(logfilename):
            with open(logfilename) as logfile:
                user_times: Dict[str, list[float]] = MyDict.parseLogFile(logfile)

                for key, value in user_times.items():
                    if key in result:
                        result[key]["Total User"] = value
                    else:
                        print(f"No key: {key} in data indices {list(result.keys())}")
        else:
            print(f"No logfile found {logfilename}")

        return result


    def __init__(self, jsonfiles: list[str], logfilename: str):
        super().update(MyTable.processMultiple(jsonfiles, logfilename))

    def toTable(self) -> pd.DataFrame:
        return pd.DataFrame.from_dict(
            { key: submap.getmeans() for key, submap in self.items() },
            orient="index"
        )


if __name__ == "__main__":
    prefix: str = os.path.commonprefix(sys.argv[1:])[:-1]
    logfilename: str = os.path.join(prefix, "submit.log")

    data: MyTable = MyTable(sys.argv[1:], logfilename)

    table: pd.DataFrame = data.toTable()
    print(tabulate(table, headers='keys', tablefmt='psql'))
    table.to_csv(prefix + "_times.csv")
