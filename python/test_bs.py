
import logging
import bs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test1(id):
    articleObj = bs.readAndProcess(id, 'https://www.haaretz.co.il/amp/' + id)
    #assertThat:
    conditions = [True
        ,articleObj.header is not None
        ,articleObj.id == id
        ,articleObj.subject is not None
        ,articleObj.sub_subject is not None
         ]
    counter = 0
    incorrect = 0 ;
    for condition in conditions:
        if not condition:
            incorrect = incorrect + 1
            logger.error("condition %d not correct", counter)
        counter = counter + 1
    if (incorrect > 0):
        logger.error("found %d incorrect conditions", incorrect)
    else:
        logger.info("%s - all is ok", id)

def test_ids(ids):
    for id in ids:
        test1(id)

if __name__ == "__main__":
    test1('1.8765533')
    test_ids(['1.8765533'
    ,'1.8764610'
    ,'1.8765443'
    ,'1.8763785'
    ,'1.8764023'
    ,'1.8763854'
     ])