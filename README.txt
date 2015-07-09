#Created by Max Candocia

# This file is part of RedditTreeGrab
#
#    RedditTreeGrab is free software: you can redistribute it and/or modify
#    it under the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RedditTreeGrab is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with RedditTreeGrab.  If not, see <http://www.gnu.org/licenses/>
#    and <http://www.gnu.org/licenses/lgpl.txt>.

PROJECT DESCRIPTION:

RedditTreeGrab is an ongoing project of mine, of which the primary component is gathering data from Reddit methodically.
The main file (which probably interests most users) is reddit_grab.py, which is a command-line program that takes 
several input parameters to produce two shelve-module files that contain thread (aka submissions/posts) information
and user information (regarding comment/post histories, karma, etc.)  

I included some files to process the data, specifically with Subreddits and n-grams.  They are far from optimized, but
I managed to use them for a project linked to at the end of this section.

The program works well if you cap the size of shelve files at about 2 GB.  Any larger and they become very slow, especially
with overwriting options enabled (-ou and -ot for overwriting user and thread information).  An option to convert the 
data to a PostgreSQL server is available, but I do not have code written for directly scraping data to a server at this time.

For the project I originally used this for, see https://www.scribd.com/doc/250044180/Analyzing-Political-Discourse-on-Reddit


FILE DESCRIPTIONS:

reddit_grab.py - This is the program that collects all the data.  It requires an updated version of PRAW.  
The Reddit API changes consistently, so there may be new bugs occasionally.  Note that large files
run very slowly due to the use of the shelve module.  I recommend using something along the lines of 

#example python code
import os
command = 'python reddit_grab.py -name test -sub politics news gaming -depth 300 -tree 100 100 2 -edate 0.2 10.0'
while True:
    os.system(command) 
    
to make things easier and safe to rare crashes

extract_ngrams.py - This will create a data structure to determine which ngrams should be collected.  It allows both
manual input and frequency-based selection.

create_ngrams_fast.py - This puts the ngrams of data into a text file for analysis.

prepare_data4.py - This prepares data for use with gen.py

gen.py - This runs a supervised, unsupervised, or semi-supervised model based on the data and any classifications that
are provided.

genmod_params.py - This file contains parameters to be used for gen.py.

get_random_users.py - This creates a file with randomly selected users so that you can add classifications to them.
Microsoft Excel hyperlink URLs are available as an option if you want to check user post histories out while having
the file open.

stopwords.txt - These are words that are removed from a dictionary if frequency-based ngram detection is allowed.

joinwords.txt - These are exceptions to stopwords if the word is not the first or last word of an ngram.

bigramjoinwords.txt - These are exceptions to stopwords if the ngram is not a unigram.

construct_user_network.py - This will construct edgelists in plaintext for thread histories.

transfer_data_to_postgres.py - This will allow you to transfer shelve module data to a PostgreSQL server.
This is a big speed advantage over the shelve module, but it is not yet integrated seamlessly into the 
reddit_grab.py file.

database_options.py - This file contains parameters for transfer_data_to_postgres.py.  This file needs to be
created by the user, but it only takes 5 lines.  It is currently omitted in this directory because it contains password
information for logging into the database server.