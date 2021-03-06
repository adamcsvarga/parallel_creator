# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 09:12:38 2017

Create pseudo sentence pairs from comparable Wikipedia articles.

@author: Adam Varga
"""

import sys
import os
import itertools

## dictionary mapping language IDs to field numbers in matching IDs file
langmap = {"en":0, "de":1, "es":2, "fr":3}

## to enable skipping to next iteration in outer loop when file not found
class ContinueI(Exception):
    pass


def read_file(filename):
    """Reads file.
    
    Args:
        filename: path of file
    
    Returns:
        lines of file
    """
    
    with open(filename, 'r') as source:
        return source.readlines()
    
def write_parallel(lang_lines):
    """Creates pseudo-parallel corpora for a given language pair.
    
    Args:
        lang_lines: dictionary with language IDs as keys and parallel article
                    lines as values
    
    """
      
    try:
        lang1, lang2 = lang_lines.keys()
    except:
        sys.stderr.write("Article does not exist for both languages, skipping...\n")
        return
    
    with open(lang1+"-"+lang2+"."+lang1, "a+") as target:
        target.write("".join(lang_lines[lang1]))
    with open(lang1+"-"+lang2+"."+lang2, "a+") as target:
        target.write("".join(lang_lines[lang2]))
    with open(lang1+"-"+lang2+".no", "a+") as target:
        target.write(str(len(lang_lines[lang1]))+'\t'+str(len(lang_lines[lang2]))+' \n')
   
        
    
def read_parallel(lang1, lang2, ids, art_dir):
    """Reads comparable parallel Wikipedia articles for a given language pair.
    
    Args:
        lang1: ID of source language
        lang2: ID of target language
        ids: lines of the matching IDs file
        art_dir: path of article directories
    
    Raises:
        ContinueI special error when a certain file is not found. This is only
        used for skipping to the next line in the matched IDs file
    """
    
    ## For stats
    paired = 0
    skipped =0
    
    start_wd = os.getcwd()
    
    try:
        abs_art_dir = os.path.abspath(art_dir)
        os.chdir(abs_art_dir)
    except:
        sys.stderr.write("Path to article directories does not exist.\n")
        exit(1)   
        
    with open(lang1+"-"+lang2+"."+lang1, "w"):
        pass
    with open(lang1+"-"+lang2+"."+lang2, "w"):
        pass
    with open(lang1+"-"+lang2+".no", "w"):
        pass

    for line in lines:
        try:
            ## Get article IDs for language pair
            lang_lines = dict()
            for lang in [lang1, lang2]:
                os.chdir(abs_art_dir)
                try:
                    field_no = langmap[lang] * 2
                except:
                    sys.stderr.write("Unknown language.\n")
                    exit(1)
                id_no = line.strip().split()[field_no]
                try:
                    os.chdir(lang+".0/plain/"+lang)
                except:
                    sys.stderr.write("Language directory does not exist.\n")
                    exit(1)
                ## Figure out base directory
                os.chdir(str(int(int(id_no)//1e+5)))
                ## Read corresponding article
                try:
                    with open(str(id_no)+"."+lang+".txt") as source:
                        lang_lines[lang] = source.readlines()
                except:
                    sys.stderr.write("File "+str(id_no)+"."+lang+".txt not found, skipping article pair...\n")
                    skipped += 1
                    raise ContinueI
            
            ## Write sentence combinations to parallel files
            os.chdir(abs_art_dir)
            write_parallel(lang_lines)
            paired += 1
        
        except ContinueI:
            continue
        
    sys.stdout.write("Finished for language pair "+lang1+"->"+lang2+".\n")
    sys.stdout.write("Paired "+str(paired)+" articles.\n")
    sys.stdout.write("Skipped "+str(skipped)+" article pairs.\n")
    
    ## Get back to scripts directory for next language pair
    os.chdir(start_wd)

if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: python parallel_creator.py <mathced IDs file> <path to article directories>\n")
        exit(1)
        
    ## Read file of matching IDs
    try:
        lines = read_file(sys.argv[1])
    except:
        sys.stderr.write("File not found.\n")
        exit(1)
        
    ## Create pseudo-parallel corpora for all language pairs
    combos = itertools.combinations(["de", "en", "es", "fr"], 2)
    
    for lang_pair in combos:
        read_parallel(lang_pair[0], lang_pair[1], lines, sys.argv[2])
        
    
