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

def process_all(data):
    """Create all the blocksize graphs"""

    keys_list : list[str] = list(data.keys());
    prefix_list : list[str]  = list(set([ key.split("_")[0] for key in keys_list]))

    first_dt = data[keys_list[0]]
    # Get all the keys
    rows_list : list[int] = first_dt['Rows'].drop_duplicates().sort_values().array
    ts_list : list[int] = first_dt['Tasksize'].drop_duplicates().sort_values().array
    cpu_list : list[int] = first_dt['cpu_count'].drop_duplicates().sort_values().array

    for prefix in prefix_list:
        for rows in rows_list:
            for cpu in cpu_list:
                gr.process_final(data, prefix, rows, cpu)


if __name__ == "__main__":
    data = gr.import_json_list(sys.argv[1:])
    process_all(data)
