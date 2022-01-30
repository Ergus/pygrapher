#!/usr/bin/env python3

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

import grapher as gr
import sys

transdic = {
    "matvec" : {
        "matvec_parallelfor_mpi" : "omp+mpi",
        "matvec_strong_flat_task_node_ompss2" : "simpler",
        "matvec_weak_fetchall_task_node_ompss2" : "optimized",
    },
    "matmul" : {
        "matmul_parallelfor_mpi" : "omp+mpi",
        "matmul_strong_nested_task_node_ompss2" : "simpler",
        "matmul_strong_flat_task_node_ompss2" : "optimized"
    },
    "jacobi" : {
        "jacobi_parallelfor_mpi" : "omp+mpi",
        "jacobi_task_fetchall_ompss2" : "ompss2 + tasks",
        "jacobi_taskfor_ompss2" : "ompss2 + taskfor"
    },
    "cholesky" : {
        "cholesky_omp_mpi" : "omp+mpi",
        "cholesky_fare_strong_ompss2" : "simpler",
        "cholesky_fare_ompss2_taskfor" : "optimized"
    }
}

def process_all(data):
    """Create all the blocksize graphs"""

    keys_list : list[str] = list(data.keys())
    prefix_list : list[str]  = list(set([ key.split("_")[0] for key in keys_list]))

    # list of all the benchmarks starting with prefix.
    for prefix in prefix_list:
        bench_list : list(str) = list(key for key in keys_list if key.startswith(prefix))
        bench_dict : Dict[str, str] =  dict(zip(bench_list, bench_list))

        print("Prefix list:", bench_list)
        rows_list : list[int] = data[bench_list[0]]['Rows'].drop_duplicates().sort_values().array
        cpu_list : list[int] = data[bench_list[0]]['cpu_count'].drop_duplicates().sort_values().array

        for rows in rows_list:
            for cpu in cpu_list:
                gr.process_final(data, bench_dict, rows, cpu, "Final")

    # list of all the benchmarks declared to translate.
    for prefix in prefix_list:
        bench_list = transdic[prefix]

        print("Prefix list traduce:", bench_list)
        first_key = list(bench_list.keys())[0]
        rows_list : list[int] = data[first_key]['Rows'].drop_duplicates().sort_values().array
        cpu_list : list[int] = data[first_key]['cpu_count'].drop_duplicates().sort_values().array

        for rows in rows_list:
            for cpu in cpu_list:
                gr.process_final(data, bench_list, rows, cpu, "Official")


if __name__ == "__main__":
    data = gr.import_json_list(sys.argv[1:])
    process_all(data)
