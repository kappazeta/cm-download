#!/bin/bash
# SRC_DIR - Directory cvat-vsm
# DATA_DIR - Directory /your/data/path/S2A_*filename*.CVAT

# ./vsm/build/bin/cvat_vsm -r /your/data/path/S2A_MSIL2A_20200529T094041_N0214_R036_T35VLF_20200529T120441.CVAT/tile_1024_4864/annotations.xml -n /your/data/path/S2A_MSIL2A_20200529T094041_N0214_R036_T35VLF_20200529T120441.CVAT/tile_1024_4864/bands.nc
if [ "$#" -ne 2 ]; then
    echo "Usage: ./rasterization.sh SRC_DIR DATA_DIR"
    exit 1
fi

SRC_DIR=$1
SRC_PATH=$SRC_DIR"/vsm/build/bin/cvat_vsm"
DATA_DIR=$2
annot_file="/annotations.xml"

for path in $DATA_DIR/*; do
    [ -d "${path}" ] || continue # if not a directory, skip
    dirname="$(basename "${path}")"
    FILE=$DATA_DIR"/"$dirname$annot_file
    BANDS_PATH=$DATA_DIR"/"$dirname"/bands.nc"
    if test -f "$FILE"; then
        $SRC_PATH -r $FILE -n $BANDS_PATH
    fi

done
