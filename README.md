# Explanation of folders

## dependency_extraction
`lucene-codecs-9.0.0.jar` is the compiled jar of the apache/lucene/codecs project found [here](https://mvnrepository.com/artifact/org.apache.lucene/lucene-codecs/versions). Version 9.0.0 is used as the current version uses jdk25 and is therefore incompatible with the JavaParser.

`output.rsf` and `output.fv` are the output of the JavaParser used on `lucene-codecs-9.0.0.jar`

`filter_rsf.py` is a script to filter `output.rsf` for dependencies strictly relevant to our group's assigned components.

## WCA
Results of WCA clustering algorithm on `filtered.rsf`

The command used to generate clusters with WCA is:

`java -Xmx4096m -jar arcade_core_clusterer.jar language=java deps=filtered.rsf projname=luccodecs projversion=9.0.0 projpath=output-cluster packageprefix="org.apache.lucene.codecs" algo=WCA measure=<UEMNM or UEM> serial=STEPCOUNT serialthreshold=1`

## Top-level files

`filtered.rsf` contains the dependencies strictly relevant to our assigned components (Result from dependency_extraction).

`prettify_output.py` is a script to make results of clustering algorithms more human readable.
