# What I have done:

## For Step 1
I normally compiled the current version with jdk25 but the compiled file is incompatible with the JavaParser used in step 2. Therefore I used an older file that still works `lucene-codecs-9.0.0.jar`.

## For Step 2
I used the JavaParser on `lucene-codecs-9.0.0.jar` with `java -jar arcade_core_JavaParser.jar lucene-codecs-9.0.0.jar ./output.rsf ./output.fv "org.apache.lucene.codecs"`.

## For Step 3
I didn't want to filter `output.rsf` manually so I wrote `filter_rsf.py` to filter the dependencies.

## For Step 4
Your task now. The .rsf file that contains the dependencies is `filtered.rsf`. Here is an example command I used to check if I did something wrong: 
`java -Xmx4096m -jar arcade_core_clusterer.jar algo=WCA language=java deps=filtered.rsf measure=UEM projname=luccodecs projversion=9.0.0 projpath=output-cluster stopthreshold=50 packageprefix="org.apache.lucene.codecs"`
