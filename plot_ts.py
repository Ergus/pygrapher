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
import pandas as pd
from typing import *


def process_all(data : Dict[str, pd.DataFrame]):
    """Create all the blocksize graphs"""

    keys_list : list[str] = list(data.keys());
    first_dt : pd.DataFrame = data[keys_list[0]]

    # Get all the keys
    rows_list : list[int] = first_dt['Rows'].drop_duplicates().sort_values().array
    ts_list : list[int] = first_dt['Tasksize'].drop_duplicates().sort_values().array
    cpu_list : list[int] = first_dt['cpu_count'].drop_duplicates().sort_values().array

    # All benchmarks
    for row in rows_list:
        for ts in ts_list:
            for cpu_count in cpu_list:
                gr.process_tasksize(data, keys_list, row, ts, cpu_count)


if __name__ == "__main__":
    data : Dict[str, pd.DataFrame] = gr.import_json_list(sys.argv[1:])
    process_all(data)
