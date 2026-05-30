# WCA
Results of WCA clustering algorithm on `filtered.rsf`

The command used to generate clusters with WCA is:

`java -Xmx4096m -jar arcade_core_clusterer.jar language=java deps=filtered.rsf projname=luccodecs projversion=9.0.0 projpath=output-cluster packageprefix="org.apache.lucene.codecs" algo=WCA measure=<UEMNM or UEM> serial=STEPCOUNT serialthreshold=1`

# ACDC
Results of ACDC clustering algorithm on `filtered.rsf`

The command used to generate clusters with ACDC is:
`java -jar .\arcade_core-ACDC.jar .\filtered.rsf .\acdc.rsf`

# LIMBO
Results of LIMBO clustering algorithm on `filtered.rsf` 

The command used to generate clusters with LIMBO is:
`java -Xmx4096m -jar arcade_core_clusterer.jar language=java \
deps=filtered.rsf projname=luccodecs projversion=9.0.0 \
projpath=output-cluster packageprefix="org.apache.lucene.codecs" \
algo=LIMBO measure=IL \
serial=STEPCOUNT serialthreshold=1`

# ARC
Results of ARC Clustering

Notebook used for generation in Google Colab: https://colab.research.google.com/drive/1BcxNk6yMSHhU35rz5Pb9aDfRTsAQuzdG?usp=sharing