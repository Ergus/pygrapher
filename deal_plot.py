
import os, sys
from typing import Dict, TextIO, Pattern, Callable, TypeAlias, NewType

from tabulate import tabulate
import pandas as pd
import matplotlib.pyplot as plt

def readPrint(name: str) -> pd.DataFrame:
    table: pd.DataFrame = pd.read_csv(name, index_col=0)
    print(name)
    print(tabulate(table, headers='keys', tablefmt='psql'))

    ax = table.plot(y=["Total Internal"], kind="barh", figsize=(10,6))
    plt.tight_layout()
    ax.get_figure().savefig(prefix + "_Internal.png")

    return table

if __name__ == "__main__":
    data: Dict[str, pd.DataFrame] = {}

    data["Autocall"] = readPrint("FlujosOut_nocal_times.csv")

    data["Sampling No Threads"] = readPrint("SamplingOut_1_times.csv")
    data["Sampling Threads"] = readPrint("SamplingOut_0_times.csv")

    data["Flows No Threads"] = readPrint("FlujosOut_1_times.csv")
    data["Flows Threads"] = readPrint("FlujosOut_0_times.csv")

    # Construct the temporal sheets
    compare_best = pd.DataFrame(index=data["Autocall"].index)

    for key, value in data.items():
        print(value.loc[:,["Total User"]])
        compare_best[key] = value["Total User"]

    compare_best.to_csv("compare_best_user_times.csv")

    print(tabulate(compare_best, headers='keys', tablefmt='psql'))

    # Grafico tiempos totales
    ax = compare_best.loc[::-1,::-1].plot(kind="barh", figsize=(10,6), width=0.8, legend='reverse')
    plt.tight_layout()
    plt.axvline(x=60, linestyle=":", color="gray", )
    ax.get_figure().savefig("Compare_User.png")
    print(f"Saving Compare_User.png")

    # Graficos contribuciones (Flows n threads)
    for key, value in list(data.items())[1:]:
        ax = data[key].loc[::-1,["Sampling", "Regressors", "HestonTotal"]].plot.barh(stacked=True, figsize=(10,6), width=0.8)
        plt.tight_layout()
        plt.axvline(x=60, linestyle=":", color="gray", )
        filename: str = "Constributions_" + key.replace(" ","_") + ".png"
        ax.get_figure().savefig(filename)
        print(f"Saving {filename}")


    # Comparaciones
    ## Autocall
    compare_nocall = compare_best.div(compare_best["Autocall"], axis=0)
    print(tabulate(compare_nocall, headers='keys', tablefmt='psql', floatfmt=".2f"))
    compare_best.to_csv("compare_nocall.csv")
    print(f"Saving compare_nocall.csv")
