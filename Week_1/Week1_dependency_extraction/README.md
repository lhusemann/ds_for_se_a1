# Explanation of files

`lucene-codecs-9.0.0.jar` is the compiled jar of the apache/lucene/codecs project found [here](https://mvnrepository.com/artifact/org.apache.lucene/lucene-codecs/versions). Version 9.0.0 is used as the current version uses jdk25 and is therefore incompatible with the JavaParser.

`output.rsf` and `output.fv` are the output of the JavaParser used on `lucene-codecs-9.0.0.jar`

`filter_rsf.py` is a script to filter `output.rsf` for dependencies strictly relevant to our group's assigned components.

`filtered.rsf` contains the dependencies strictly relevant to our assigned components. The result of `filter_rsf.py`.