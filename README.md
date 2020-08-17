# cvat-download
Script to download CVAT annotations to tiles directories.

## Setup

1. Clone the CVAT repository if you don't have it yet.

        git clone https://github.com/kappazeta/cvat.git

2. Enter the directory of the `cvat-download` repository.

3. Create a conda environment for the CVAT CLI utility.

        conda env create -f environment.yml
    
## Configuration

The script expects an S2 product directory which has been subtiled and converted, using `cvat-vsm` (<https://github.com/kappazeta/cvat-vsm.git>).

In the `cvat-vsm` output directory, `cvat-download` expects to find a configuration file `cvat-tup.cfg` and a label classes definition file `classes.json`. In the case that these files don't exist yet, `cvat-download` creates them from templates.

An example `cvat-tup.cfg` file:

```
cvat_host_addr=localhost
cvat_host_port=8080
cvat_credentials=YOUR_CVAT_USERNAME:YOUR_CVAT_PASSWORD
cvat_cli_path=/YOUR_PATH_TO_CVAT_WORKING_COPY/utils/cli/cli.py
git_repository=https://github.com/kappazeta/cvat_cloudmask_annotations.git
```

Here, `YOUR_PATH_TO_CVAT_WORKING_COPY`, `YOUR_CVAT_USERNAME` and `YOUR_CVAT_PASSWORD` ought to be replaced with values which correspond to your setup.

An example `classes.json` file:

```
[
    {   
        "name": "CLEAR",
        "attributes": []
    },  
    {   
        "name": "CLOUD_SHADOW",
        "attributes": []
    },  
    {   
        "name": "CLOUD",
        "attributes": []
    },  
    {   
        "name": "SEMI_TRANSPARENT_CLOUD",
        "attributes": []
    }   
]
```

##  Running

1. Activate the conda environment

        source activate cvat-cli

2. Run the script with the output directory of `cvat-vsm` as the only argument. Note that the path should end with the suffix `.CVAT`.

        ./bin/cvat-download.sh YOUR_PATH
