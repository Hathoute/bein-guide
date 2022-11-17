# BEIN-Sports Guide

A python3 script that scraps BEIN Sports guide page and outputs an XMLTV file.

### How to use
0. Make sure you have python3 and pip3 (if not, just edit **routine.sh** with your commands)
1. Clone this repository

`https://github.com/Hathoute/bein-guide`
2. Make **routine.sh** executable

`chmod +x routine.sh`
3. Run **routine.sh**

You might want to edit the bash script to customize it
- Specify output path (default: **bein.xmltv**)
- Specify number of days to grab (default: **3**)

You might also want to add a cronjob, so that the script generates the guide everyday at 6AM for example

`0 6 * * * /full/path/to/routine.sh`

### Enhacements
- Use a built-in request handler and HTML parser rather than [selenium with a web driver running in a docker container 
using the host's shared memory](https://i.kym-cdn.com/entries/icons/original/000/028/139/cover.jpg).
- Load a file that maps guide channel names to user defined names.
- Pretty print the resulted XMLTV file?