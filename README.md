# unlod
Linked open data platform serving the UNBIS Thesaurus. See it in action here: http://52.20.172.127/ No guarantees that it's up at any given time.

Uses RDFLib with a Sleepycat (dbd) store.

Code seems to work on Python3x (tested on 3.4), but there may be some issues in a few of the external libraries.

Note I am using some libraries that didn't play nicely with Python3. I've forked them and made enough changes to them so that they work for my purposes. They might not work for yours.

* https://github.com/aaronhelton/django-pure-pagination
* https://github.com/aaronhelton/elasticpy

There is no quickstart. This isn't really intended to be reused by others, but the code could serve as a reference in case others want to learn.

I still have a good deal of cleanup to do and some management commands to write. 
