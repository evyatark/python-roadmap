'''

Demonstrating splitting the Python code to several modules.
Make sure that the Dockerfile copies all modules (.py files) into the docker image!

'''


def remove_duplicates(article_ids):
    set = {'0'}
    for id in article_ids:
        newId = id
        if ('#' in id):
            newId = id[:id.find('#')]
        if ('?' in id):
            newId = id[:id.find('?')]
        set.add(newId)
        if ('?' in newId):
            logger.warn("url %s still contains ?, original was %s", newId, id)
    set.remove('0')
    return list(set)




if __name__ == "__main__":
    list = remove_duplicates(["one", "two", "one"])
    print(list)

