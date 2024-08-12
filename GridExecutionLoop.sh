#!/bin/bash

# ./protoGridTest.sh -e ../Murex_Master/dist/win64/debug/bin/ProtoGridLauncher.exe -i inputs -o output1 -s EqFxManagerProtoGridService -m Valuate -c soam_client_data.json

source ArgParseBash/argparse.sh

add_argument -a e -l executable -h "ProtoGridLauncher file" -t file
add_argument -a p -l parallel -h "Parallel" -t bool
add_argument -a c -l connection -h "Connection file" -t file
add_argument -a i -l inputdir -h "Requests dir" -t path
add_argument -a o -l outputdir -h "Responses dir" -t path
#add_argument -a s -l service -h "Service name" -t string
#add_argument -a m -l method -h "Method name" -t string
add_argument -a r -l repeats -h "Repeat executions" -t int

parse_args "$@"

# Redirect all the outputs to the logfile
exec &> >(tee -a ${ARGS[o]}/submit.log)

echo -e "\n# Before (default)"
printargs "# "

start_time=$SECONDS

for input in ${ARGS[i]}/*.json; do
    bname="${input##*/}"                             # get only filename no path base.json
    for ((i=0; i < ${ARGS[r]}; i++)); do
        output="${ARGS[o]}/${bname//.json/_result_${i}.json}" # output file name out/base_result.json
        command="${ARGS[e]} -c ${ARGS[c]} -i ${input} -o ${output} 2>&1" 
        echo "# Command: ${command}"

        if ${ARGS[p]}; then
            ${command} &
        else
            ${command}
        fi
    done
done

if ${ARGS[p]}; then
    echo "# Waiting jobs:"
    jobs -pl
    wait
fi

echo "# Total time is $(( SECONDS - start_time ))"


