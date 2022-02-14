# Copyright (C) 2022  Ergus

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os
import json
import pandas as pd
import numpy as np
import pprint
import pickle
from typing import *

from collections.abc import Callable

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.style'] = 'normal'
plt.rcParams['font.size'] = '8'

pd.set_option('display.max_rows', None)

colors_bs = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.BASE_COLORS.values())

get_complexity : Dict[str, Callable[[int], float]] = {
    "cholesky" : lambda x: (x**3)/3.0,
    "matmul" : lambda x: x**3,
    "matvec" : lambda x: x**2,
    "jacobi" : lambda x: x**2
}


def save_all_files(filename: str, fig):
    """Save the graphs to two files."""

    # Save the plots with pickle to recover them:
    #
    # import matplotlib.pyplot as plt
    # import pickle
    # with open('filename.pkl', 'rb') as pkl:
    #     ax = pickle.load(pkl)
    # plt.show()
    with open(filename + ".pkl",'wb') as pkl:
        pickle.dump(fig, pkl)

    # Save the image as a png
    fig.savefig(filename + ".png",
                dpi=300,
                format='png',
                #bbox_extra_artists=[leg],
                bbox_inches='tight')

    print("Generated:", filename)


def import_json_list(input_list : list[str]) -> Dict[str, pd.DataFrame]:
    '''Imports a group of json files containing experiment results'''

    data : Dict[str, pd.DataFrame] = {}

    if not input_list:
        raise ValueError("Imput list is empty.")

    for fname in input_list:

        if fname.split(".")[-1] != "json":
            print("Import ignores:", fname, \
                  "because it is not a json", file = sys.stderr)
            continue

        try:
            print("Loading:", fname, end="... ")

            with open(fname, 'r') as f:
                fdata = json.load(f)

                # key is the experiment: cholesky_fare_ompss2_taskfor
                for key in fdata:

                    # data to Pandas Dataframe
                    df_in: pd.DataFrame = pd.DataFrame(fdata[key])

                    if key in data:
                        data[key] = pd.concat([data[key], df_in], ignore_index=True)
                    else:
                        data[key] = df_in

            print("Done")

        except IOError:
            print("File not accessible or json corrupt", file = sys.stderr)

    return data


def add_time(ax, dt_ts : pd.DataFrame, label: str, colorname : str):
    "Add raw data graph"
    if dt_ts.empty:
        print("Ignoring:", label, "is empty", file = sys.stderr)
        return

    dt_sorted : pd.DataFrame = dt_ts.sort_values(by='worldsize')
    x : pd.Series = dt_sorted['worldsize']

    y : pd.Series = dt_sorted['Algorithm_time']
    erry : pd.Series = dt_sorted['Algorithm_time_stdev'].divide(dt_sorted['executions']**(1/2))

    ax.errorbar(x, y, yerr = erry, fmt = 'o-',
                linewidth=0.75, color=colorname,
                markersize=2, label=label)


def add_scalability(ax, dt_ts : pd.DataFrame, label: str, colorname : str):
    """Add lines to the graphs."""
    if dt_ts.empty:
        print("Ignoring:", label, "is empty", file = sys.stderr)
        return

    row_one : pd.DataFrame = dt_ts.loc[dt_ts['worldsize'] == 1]
    if len(row_one.axes[0]) != 1:
        print("Single node problem for:", label, file = sys.stderr)
        print("Input data:")
        print(dt_ts)
        return

    dt_sorted : pd.DataFrame = dt_ts.sort_values(by=['worldsize'])
    x : pd.Series = dt_sorted['worldsize']

    one : float = row_one['Algorithm_time'].values[0]
    errone : float = (row_one['Algorithm_time_stdev'] / (row_one['executions']**(1/2))).values[0]

    # Error
    y  : pd.Series = dt_sorted['Algorithm_time']
    erry : pd.Series = dt_sorted['Algorithm_time_stdev'].divide(dt_sorted['executions']**(1/2))

    sy : pd.Series = one / dt_sorted['Algorithm_time']
    errsy : pd.Series = sy * (erry/y + errone/one)

    ax.errorbar(x, sy, errsy, fmt ='o-',
                linewidth=1, color=colorname,
                markersize=2, label=label)


def add_performance(ax, dt : pd.DataFrame,
                    label: str, colorname : str):
    """Add lines to the graphs."""
    if dt.empty:
        print("Ignoring: ", label, "is empty", file = sys.stderr)
        return

    assert 'GFLOPS' in dt.columns
    assert 'GFLOPS_ERR' in dt.columns

    ax.errorbar(dt['worldsize'], dt['GFLOPS'], dt['GFLOPS_ERR'],
                fmt='o-',
                linewidth=1, color=colorname,
                markersize=2, label=label)

def filter_rtc(dt : pd.DataFrame, **kwargs) -> pd.DataFrame:
    '''Filter df_key by the criteria in argv'''
    query : str = ""
    for key, value in kwargs.items():
        if key in dt:
            if query: query += " & "
            query += "{} == {}".format(key, value)

    return dt.query(query)


def filter_min(dt : pd.DataFrame) -> pd.DataFrame:
    '''Get the rows with minimum time/worldsize'''
    assert (not "iterations" in dt) or (dt["Iterations"].nunique() == 1)
    return dt.loc[dt.groupby('worldsize')['Algorithm_time'].idxmin()].sort_values(by=['worldsize']).copy()


def get_performance_table(dt : pd.DataFrame, complexity : float) -> pd.DataFrame:
    assert not dt.empty

    time_per_iter : pd.Series = dt['Algorithm_time'].copy()

    if "Iterations" in dt.columns:
        assert dt["Iterations"].nunique() == 1
        time_per_iter /= dt["Iterations"]

    dt = dt.filter(['worldsize', 'Rows', 'Tasksize', 'executions', 'Iterations',
                    'Algorithm_time', 'Algorithm_time_stdev', 'cpu_count'],
                   axis=1)

    dt['Time_per_it'] = time_per_iter
    dt['Complexity'] = complexity
    dt['GFLOPS'] = complexity / time_per_iter
    dt['GFLOPS_ERR'] = dt['GFLOPS'] * dt['Algorithm_time_stdev'] / dt['Algorithm_time']

    return dt


def process_tasksize(data : Dict[str, pd.DataFrame],
                     keyslist:list,
                     rows:int,
                     ts:int,
                     cpu_count:int) -> None:
    """Create graphs time vs tasksize"""

    fig, axs = plt.subplots(nrows=3, sharex=True, sharey=False,
                            gridspec_kw={"hspace": 0})

    axs[0].set_ylabel("Time")
    axs[1].set_ylabel("Scalability")
    axs[2].set_ylabel("Performance (Gflops)")

    for ax in axs:
        ax.grid(color='b', ls = '-.', lw = 0.25)

    axs[0].set_yscale('log')
    axs[2].set_xlabel('Nodes')

    fig.suptitle(keyslist[0].split("_")[0] + " " +
                 str(rows) + " x " + str(ts) +
                 " (" + str(cpu_count) + " cores)")

    color_index : int = 0

    for key in data:
        dt = filter_rtc(data[key],
                        Rows=rows,
                        Tasksize=ts,
                        cpu_count=cpu_count)

        prefix : str = key.split("_")[0]
        label : str = " ".join(key.split("_")[1:]) # "cholesky_memory_ompss2" -> "memory ompss2"

        complexity : float = get_complexity[prefix](rows)

        if key.endswith("mpi"):
            dt = dt.drop_duplicates(subset='worldsize')

            color = colors_bs[color_index]
            color_index = color_index  + 1

            add_time(axs[0], dt, label, color)
            add_scalability(axs[1], dt, label, color)

            dt_perf : pd.DataFrame = get_performance_table(dt, complexity)
            add_performance(axs[2], dt_perf, label, color)
        else:
            for ns in range(2):
                color = colors_bs[color_index]
                color_index = color_index + 1

                dt_ns = filter_rtc(dt, namespace_enabled=ns)
                labelns = label + [" nons", " ns"][ns]

                add_time(axs[0], dt_ns, labelns, color)
                add_scalability(axs[1], dt_ns, labelns, color)

                dt_perf_ns : pd.DataFrame = get_performance_table(dt_ns, complexity)
                add_performance(axs[2], dt_perf_ns, labelns, color)

    plt.legend(bbox_to_anchor=(1,1),
               loc='center left', fontsize='x-small',
               fancybox=True, shadow=True, ncol=1)

    # Save image file.
    filename = "Scalability_" \
        + key.split("_")[0] + "_" \
        + str(rows) + "_" \
        + str(ts) + "_" \
        + str(cpu_count)

    save_all_files(filename, fig)
    plt.close()


def process_experiment(dt : pd.DataFrame,
                       label : str,
                       rows : int,
                       ts_list : list[int],
                       cpu_list : list[int]):
    """Create graphs comparing all the TS for same size and num_cpus"""

    print("= Plot:", label, rows)
    fig, axs = plt.subplots(nrows=3, ncols=(len(cpu_list)),
                            sharex=True, sharey="row",
                            gridspec_kw={"hspace": 0, "wspace": 0})

    # Title
    fig.suptitle(label + " " + str(rows))
    nodes_list : list[int] = dt['worldsize'].drop_duplicates().sort_values().array

    axs[0,0].set_ylabel("Time")
    axs[1,0].set_ylabel("Scalability")
    axs[2,0].set_ylabel("Performance(GFLops)")

    prefix : Final[str] = label.split("_")[0]
    complexity : Final[float] = get_complexity[prefix](rows)

    dt_rows = filter_rtc(dt, Rows=rows, namespace_enabled=1)

    for i in range(len(cpu_list)):
        cores : int = cpu_list[i]
        print("== Plotting for:", cores, "cores")

        for ax in axs[:,i]:
            ax.grid(color='b', ls = '-.', lw = 0.25)

        axs[0,i].title.set_text(str(cores) + "cores")
        axs[0,i].set_yscale('log')
        axs[0,i].set_xticks(nodes_list)

        axs[2,i].set_xlabel('Nodes')

        dt_rows_cpu = filter_rtc(dt_rows, cpu_count=cores)

        color_index : int = 0
        for ts in ts_list:
            linelabel : str = str(ts)
            color = colors_bs[color_index]
            color_index = color_index + 1

            dt_rows_cpu_ts = filter_rtc(dt_rows_cpu, Tasksize=ts)
            dt_rows_cpu_ts = filter_min(dt_rows_cpu_ts)

            add_time(axs[0,i], dt_rows_cpu_ts, linelabel, color)
            add_scalability(axs[1,i], dt_rows_cpu_ts, linelabel, color)

            st_perf = get_performance_table(dt_rows_cpu_ts, complexity)
            add_performance(axs[2,i], st_perf, linelabel, color)

        axs[0,i].legend(loc='upper right',
                        fontsize='x-small',
                        fancybox=True, shadow=True, ncol=2)

        axs[1,i].legend(loc='upper left',
                        fontsize='x-small',
                        fancybox=True, shadow=True, ncol=2)


        axs[2,i].legend(loc='upper left',
                        fontsize='x-small',
                        fancybox=True, shadow=True, ncol=2)

    plt.subplots_adjust()

    # Save image file.
    filename = "Compare_" + label + "_" + str(rows)
    save_all_files(filename, fig)
    plt.close()


def process_final(data : Dict[str, pd.DataFrame],
                  bench_dict : Dict[str, str],
                  rows : int,
                  cores : int,
                  fileprefix : str):
    "Graphs for final doc"

    tmp : list[str] = list(set([ key.split("_")[0] for key in bench_dict.keys()]))
    assert(len(tmp) == 1)
    prefix : Final[str] = tmp[0]

    print("Processing:", prefix, rows, cores)
    complexity : Final[float] = get_complexity[prefix](rows)

    fig, ax = plt.subplots()
    ax.set_xlabel("Number of nodes")
    ax.set_ylabel("Performance (GFLOPS/sec)")

    color_index : int = 0
    for bench_name, label in bench_dict.items():
        assert bench_name.startswith(prefix)
        dt : pd.DataFrame = filter_rtc(data[bench_name],
                                       Rows=rows,
                                       cpu_count=cores,
                                       namespace_enabled=1)
        dt = filter_min(dt)

        dt_perf : pd.DataFrame = get_performance_table(dt, complexity)

        add_performance(ax, dt_perf, label, colors_bs[color_index])
        color_index = color_index + 1

        if bench_name == label:
            print(bench_name)
            print(dt_perf)
            fname : str = bench_name + "_" + str(rows) + "_" + str(cores)
            dt_perf.to_csv(fname + ".csv", index = False)


    filename : str = fileprefix + "_" + prefix + "_" + str(rows) + "_" + str(cores)
    plt.legend(loc='upper left', fontsize='medium',)
    save_all_files(filename, fig)
