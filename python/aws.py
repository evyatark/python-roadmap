'''

Demonstrating splitting the Python code to several modules.
Make sure that the Dockerfile copies all modules (.py files) into the docker image!

'''

import boto3
from botocore.client import Config
import os

# take secret keys from environment.
# you should add them to your env withthese linux commands: 
#export ACCESS_KEY_HERE='ABCDEFGHIJKLMNOPQRST'
#export PRIVATE_LONG_KEY_HERE='abcdefghijklmnopqrstuvwxyzabcdefghijklmn'
ACCESS_KEY_HERE = os.environ['ACCESS_KEY_HERE']
PRIVATE_LONG_KEY_HERE = os.environ['PRIVATE_LONG_KEY_HERE']

# http://web-scraping-1.s3-website-us-east-1.amazonaws.com/haaretz/index.html

def access_aws():
    # Initialize a session using AWS Buckets.
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name='us-east-1',
                            aws_access_key_id=ACCESS_KEY_HERE,
                            aws_secret_access_key=PRIVATE_LONG_KEY_HERE)

    # List all buckets on your account.
    response = client.list_buckets()
    spaces = [space['Name'] for space in response['Buckets']]
    print("Buckets List: %s" % spaces)
    dict1 = client.list_objects_v2(Bucket='web-scraping-1', MaxKeys=3, Prefix='ind')
    print ("Top Level index file: %s" % dict1)  # TODO pretty print
    print("\n\n\n")
    dict2 = client.list_objects_v2(Bucket='web-scraping-1', MaxKeys=10, Prefix='haaretz/ind')
    print ("index files: %s" % dict2)   # TODO pretty print



if __name__ == "__main__":
    access_aws()

'''
{
	"ResponseMetadata": {
		"RequestId": "E5CA7E169DC4EB43",
		"HostId": "f69DYKaS9pMQk+f9gVzKnUqBD7q5uC+3rez+N0ytjF4uwdv1gfkMz0FY0zjTZrEC18uHulDR4h8=",
		"HTTPStatusCode": 200,
		"HTTPHeaders": {
			"x-amz-id-2": "f69DYKaS9pMQk+f9gVzKnUqBD7q5uC+3rez+N0ytjF4uwdv1gfkMz0FY0zjTZrEC18uHulDR4h8=",
			"x-amz-request-id": "E5CA7E169DC4EB43",
			"date": "Thu, 21 May 2020 20:17:25 GMT",
			"x-amz-bucket-region": "us-east-1",
			"content-type": "application/xml",
			"transfer-encoding": "chunked",
			"server": "AmazonS3"
		},
		"RetryAttempts": 0
	},
	"IsTruncated": false,
	"Contents": [{
		"Key": "haaretz/index.html",
		"LastModified": "datetime.datetime(2020, 5, 21, 18, 57, 53, tzinfo = tzutc())",
		"ETag": "b7e309686e17db45125708b8f08ae944",
		"Size": 755,
		"StorageClass": "STANDARD"
	}, {
		"Key": "haaretz/index_2020_05_08.html",
		"LastModified": "datetime.datetime(2020, 5, 17, 16, 48, 30, tzinfo = tzutc())",
		"ETag": "f292e39041e08e901dfe690219ed85c6",
		"Size": 36462,
		"StorageClass": "STANDARD"
	}, {
		"Key": "haaretz/index_2020_05_09.html",
		"LastModified": "datetime.datetime(2020, 5, 17, 17, 12, 47, tzinfo = tzutc())",
		"ETag": "f292e39041e08e901dfe690219ed85c6",
		"Size": 36462,
		"StorageClass": "STANDARD"
	}, {
		"Key": "haaretz/index_2020_05_21.html",
		"LastModified": "datetime.datetime(2020, 5, 21, 19, 31, 12, tzinfo = tzutc())",
		"ETag": "70009 de70d637b563474a2a487e0c8d1",
		"Size": 72053,
		"StorageClass": "STANDARD"
	}],
	"Name": "web-scraping-1",
	"Prefix": "haaretz/ind",
	"MaxKeys": 10,
	"EncodingType": "url",
	"KeyCount": 4
}
'''