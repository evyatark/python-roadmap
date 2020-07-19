#
# A Python script
# to compare 2 directories
# and find sub-dirs and files with (almost) identical names
#

import os
import logging
import re

ROOT1 = '/home/evyatar/Downloads/newBooks/'
#ROOT1 = '/home/evyatar/Downloads/books2/2019a (books2019a at gmail)/'
#ROOT1 = '/home/evyatar/Downloads/books2/books 2015-2018/'
ROOT2 = '/home/evyatar/Downloads/books2/single/'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def publishers():
    return [
        "Apress"
        , "Packt"
        , "Manning"
        , "O'Reilly"
        , "CRC"
        , "Unknown"
        , "Leanpub"
        , "Pragmatic"
        , "No Starch"
        , "Wiley"
        , "Wrox"
        , "ACM"
        , "GoalClicker"
        , "Pearson"
        , "Addison Wesley"
        , "Fullstack"
        , "Amazon"
        , "Workman"
        , "Artima"
        , "RockRidge"
        , "GetiPub"
        , "Razeware"
        , "Ninja"
        , "AI"
        , "Springer"
        , "Sitepoint"
        , "SitePoint"
        , "Cambridge"
        , "McGraw Hill"
        , "BEP"
        , "Webucator"
        , "Academic"
        , "Academic Press"
        , "Prometheus"
        , "Underscore"
    ]

def isEpub(book):
    return True


def is_epub(file_name) :
    return is_of_type(file_name, "epub")

def is_pdf(file_name) :
    return is_of_type(file_name, "pdf")

def is_of_type(file_name, type) :
    return os.path.isfile(file_name) and file_name.endswith("." + type)

# Finds epub and pdf files in the given directory
# returns a tuple of 2 lists: pdfs and epubs
def find_pdf_epub_files(full_dir_name):
    all_files_in_dir = (os.listdir(full_dir_name))
    epubs = []
    pdfs = []
    for item in all_files_in_dir:
        if is_epub(full_dir_name + "/" + item):
            epubs.append(item)
        if is_pdf(full_dir_name + "/" + item):
            pdfs.append(item)
    #return filter(isEpub, all_files_in_dir)
    return (pdfs, epubs)

def find_singles_in_dirs(list_of_root_dirs):
    all = []
    for d in list_of_root_dirs:
        all = all + find_singles(d)
    return all

def find_singles(root_dir):
    if not os.path.exists(root_dir) or not os.path.isdir(root_dir):
        #logger.warning("dir %s does not exist or is not a directory", root_dir)
        pass
    path = os.path.abspath(root_dir)        # this is without trailing /
    all_files_in_dir = (os.listdir(path))
    all_items = []
    for item in all_files_in_dir:
        # in each item (sub-dir of root) - expect the item to be a dir with epub and pdf
        full_file_name = path + "/" + item
        x = is_book_single(full_file_name)
        if x:
            itemJson = {}
            itemJson["name"] = item
            itemJson["full_dir_path"] = full_file_name
            itemJson["has_pdf"] = ".pdf" in item
            itemJson["has_epub"] = ".epub" in item
            all_items.append(itemJson)

    #display_list_of_items(all_items, path)
    sorted_list_of_titles = sorted (list(map(lambda item: item["name"], all_items)))
    #for name in sorted_list_of_titles:
    #    logger.info(name)
    return sorted_list_of_titles

def find_single_file_dir(file_name, list_of_root_dirs):
    for dir in list_of_root_dirs:
        for file in os.listdir(os.path.abspath(dir)):
            if os.path.isfile(os.path.abspath(dir) + "/" + file) and (file == str(file_name)):
                return os.path.abspath(dir)
    return ""



def traverse(root_dir):
    if not os.path.exists(root_dir) or not os.path.isdir(root_dir):
        #logger.warning("dir %s does not exist or is not a directory", root_dir)
        pass
    #logger.info(os.path.abspath(root_dir))
    path = os.path.abspath(root_dir)        # this is without trailing /
    all_files_in_dir = (os.listdir(path))
    all_items = []
    for item in all_files_in_dir:
        # in each item (sub-dir of root) - expect the item to be a dir with epub and pdf
        full_file_name = path + "/" + item
        x = is_book_dir(full_file_name)
        if (not x):
            #logger.warning ("unknown publisher name: %s", full_file_name)
            pass
        if os.path.isdir(full_file_name) and not is_book_dir(full_file_name):
            #dive into dir
            #print("deeper into " + full_file_name)
            #logger.warning("deeper into %s", full_file_name)
            all_items = all_items + traverse(full_file_name)
        if os.path.exists(full_file_name):
            if (os.path.isdir(full_file_name)):
                dir_name = full_file_name
                #logger.info("dir: %s", full_file_name)
                (pdfs, epubs) = find_pdf_epub_files(dir_name)
                itemJson = {}
                itemJson["name"] = item
                itemJson["full_dir_path"] = dir_name
                itemJson["has_pdf"] = False
                itemJson["has_epub"] = False
                if pdfs or epubs:
                    #logger.info("dir: %s", dir_name)
                    if pdfs:
                        #logger.info("pdf: %s", pdfs)
                        itemJson["has_pdf"] = True
                    if epubs:
                        #logger.info("epub: %s", epubs)
                        itemJson["has_epub"] = True
                itemJson["pdfs"] = pdfs
                itemJson["epubs"] = epubs
                all_items.append(itemJson)
            else:
                #logger.info("not dir: %s", full_file_name)
                pass
    display_list_of_items(all_items, path)
    # if len(all_items) > 0:
    #     logger.info("-------------------")
    #     logger.info(path)
    #     logger.info("I have %s items", str(len(all_items)))
    #     #for itemJson in all_items:
    #     #logger.info("I have %s pdfs",str(len(list(filter(lambda item: item["has_pdf"] ,all_items)))))
    #     both = list(filter(lambda item: item["has_epub"] and item["has_pdf"], all_items))
    #     logger.info("I have %s both", str(len(both)))
    #     only_pdf = list(filter(lambda item: item["has_pdf"] and not item["has_epub"] ,all_items))
    #     logger.info("I have %s only pdfs",str(len(only_pdf)))
    #     only_epub = list(filter(lambda item: item["has_epub"] and not item["has_pdf"] ,all_items))
    #     logger.info("I have %s only epubs",str(len(only_epub)))
    #     logger.info("I have %s none",str(len(list(filter(lambda item: not item["has_epub"] and not item["has_pdf"] ,all_items)))))
    #     logger.info("only epubs: %s", only_epub)
    return all_items

def display_list_of_items(all_items, path):
    if not logger.isEnabledFor(logging.DEBUG):
        return
    if len(all_items) > 0:
        logger.info("-------------------")
        logger.info(path)
        logger.info("I have %s items", str(len(all_items)))
        #for itemJson in all_items:
        #logger.info("I have %s pdfs",str(len(list(filter(lambda item: item["has_pdf"] ,all_items)))))
        both = list(filter(lambda item: item["has_epub"] and item["has_pdf"], all_items))
        logger.info("I have %s both", str(len(both)))
        only_pdf = list(filter(lambda item: item["has_pdf"] and not item["has_epub"] ,all_items))
        logger.info("I have %s only pdfs",str(len(only_pdf)))
        only_epub = list(filter(lambda item: item["has_epub"] and not item["has_pdf"] ,all_items))
        logger.info("I have %s only epubs",str(len(only_epub)))
        logger.info("I have %s none",str(len(list(filter(lambda item: not item["has_epub"] and not item["has_pdf"] ,all_items)))))
        #logger.info("only epubs: %s", only_epub)
        logger.info("both: %s", both)
        for item in both:
            if not is_book_dir2(item):
                #logger.warning("item incomplete - %s %s", item["name"], item)
                pass



def I_have_pdf(itemJson):
    x = itemJson["has_pdf"]
    #print(x)
    #if not x:
    #    print(x)
    return (x == True)


def is_book_name(full_file_name):
    #dir = os.path.dirname(full_file_name)
    leaf_dir = os.path.basename(full_file_name)
    #result = leaf_dir.startswith("Apress")
    result = leaf_dir.rsplit(" (")[0] in publishers()
    result = result and is_year(leaf_dir)
    return result

def is_year(name):
    return re.search(" \(\d\d\d\d\) - ", name) is not None

def is_book_dir(full_file_name):
    return os.path.exists(full_file_name) and os.path.isdir(full_file_name) and is_book_name(full_file_name)

def is_book_single(full_file_name):
    return os.path.exists(full_file_name) and os.path.isfile(full_file_name) and is_book_name(full_file_name)

def is_book_dir2(itemJson):
    # itemJson["name"] = item
    # itemJson["full_dir_path"] = dir_name
    # itemJson["has_pdf"] = False
    # itemJson["has_epub"] = False
    if os.path.exists(itemJson["full_dir_path"]) \
            and is_book_name(itemJson["full_dir_path"]) \
        and itemJson["has_pdf"] and itemJson["has_epub"] \
        and (itemJson["name"] + ".pdf") in itemJson["pdfs"] \
        and (itemJson["name"] + ".epub") in itemJson["epubs"]:
        return True
    else:
        return False


def find_title_in_dirs(name, all_Indirs):
    result = []
    #logger.info("checking singles:%s against %s items", name, str(len(all_Indirs)))
    for item in all_Indirs:
        if (item["name"] + ".epub" == str(name)) or (item["name"] + ".pdf" == str(name)):
            #if (item["name"].startswith("Addison") and str(name).startswith("Addison")):
            #logger.info("found %s %s", name, item)
            x = ""
            if item["has_pdf"]:
                x="pdf"
            else:
                x="epub"
            path = find_single_file_dir(name, single_dirs)
            result.append([path + "/" + name, item["full_dir_path"] + " " + x])
    return result

single_dirs = [
        '/home/evyatar/Downloads/books2/single/',
        '/home/evyatar/Downloads/books2/books 2015-2018/2018 [27GB]/single [3G]/',
        '/home/evyatar/Downloads/books2/2019b/']


def compare(root_dir):
    all_Indirs = traverse(root_dir)
    # single_dirs = [
    #     '/home/evyatar/Downloads/books2/single/',
    #     '/home/evyatar/Downloads/books2/books 2015-2018/2018 [27GB]/single [3G]/',
    #     '/home/evyatar/Downloads/books2/2019b/']
    #all_singles = find_singles(ROOT2)
    all_singles = find_singles_in_dirs(single_dirs)
    all_results = []
    for name in all_singles:
        all_results = all_results + find_title_in_dirs(name, all_Indirs)
    return str(all_results).replace("],", "\n")

def main():
    #all_Indirs = traverse(ROOT1)
    #display_list_of_items( traverse(ROOT1), ROOT1 )
    #all_singles = find_singles(ROOT2)
    list = [ROOT1, "/home/evyatar/Downloads/books2/2019a (books2019a at gmail)", "/home/evyatar/Downloads/books2/2020",
            "/home/evyatar/Downloads/books2/books 2015-2018/2018 [27GB]/a [elayneTrakand03 at gmail]",
            "/home/evyatar/Downloads/books2/books 2015-2018/2018 [27GB]/b [privateEvyatar15 at gmail]",
            "/home/evyatar/Downloads/books2/books 2015-2018/2018 [27GB]/c [1G]"]
    for root in list:
        result1 = compare(root)
        logger.info(" for %s result is:\n %s", root, result1)


if __name__ == "__main__":
    main()
