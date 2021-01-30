import csv
import boto3
import time
import requests
import json
import random
from town_to_zip import zips

# BOTO3 S3 docs
# https://boto3.amazonaws.com/v1/documentation/api/1.9.42/reference/services/s3.html#S3.Client.copy

# BOTO3 Polly docs
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/polly.html

# Megaphone API docs
# https://developers.megaphone.fm/

aws_polly_profile_name = 'FILL THIS OUT' # An AWS profile name, with proper Polly and S3 perms
org_guid = 'FILL THIS OUT' # your megaphone org guid
podcast_guid = 'FILL THIS OUT' # the guid of the podcast to which you're attaching the pre-roll
token = 'FILL THIS OUT' # megaphone token for the user who will be creating the promos and pre-rolls
bucket = 'FILL THIS OUT' # publicly readable S3 bucket

# API URL to create a promo
promo_url = "https://cms.megaphone.fm/api/organizations/" + org_guid + "/promos"

# We like Matthew, but there are many more to choose from
# See: https://docs.aws.amazon.com/polly/latest/dg/voicelist.html
voice_id = 'Matthew'

session = boto3.Session(profile_name=aws_polly_profile_name)
polly = session.client('polly')
s3 = session.client('s3')

# THESE NEED TO BE CHANGED
# EVERY TIME YOU CHNAGE DATA
date = "2020-01-28" # start of experiment
start = "2021-01-28T18:00:00" # Start of promos
end = "2021-01-31T18:00:00" # End of promos

# Load up csv and get data for each town
towns = []
with open('covid_weekly_data.csv', 'r') as dest:
	reader = csv.reader(dest)
	for line in reader:
		towns.append(line)

updates = {}

for town in towns:
	# Pick out only the pieces of data that you'll be interpolating into the script
	city_town, total_cases, two_week_cases, avg_daily_rate, color, change, pos_test_rate = town[0], town[3], town[4],town[5], town[6], town[7], town[11]
	# Might require some logic to make the script more smooth (also prevents ssml errors)
	if total_cases == "<5":
		total_cases = 'fewer than five'
	if two_week_cases == "<5":
		two_week_cases = 'fewer than five'
	
	if change == 'Higher':
		change = 'is higher than'
	elif change == 'Lower':
		change = 'is lower than'
	else:
		change == 'hasn’t changed since'
	
	# Template for the script
	# We use it to create a unique COVID update for each town in MA
	# domain name='news' means it will use the "newscaster" style
	# https://docs.aws.amazon.com/polly/latest/dg/using-newscaster.html
	msg = f"""
	<speak> 
	<amazon:domain name='news'>
	Before we get to Coronavirus Briefly, here's the latest data for {city_town} from the Massachusetts Department of Public Health. There have been {total_cases} total cases of COVID. In the past two weeks, there have been {two_week_cases} cases. The risk level for {city_town} is currently in the {color}. The positive test rate is at {pos_test_rate}, which {change} last week. For more details, visit W.B.U.R. dot org slash coronavirus. <break time='1s'/>
	</amazon:domain> 
	</speak>
	"""
	
	# All updates, key is the unique town name
	updates[city_town] = msg

# Loop through all the updates
for key in updates:
	response = polly.start_speech_synthesis_task(
		Engine= 'neural', # need this for newscaster style
		OutputFormat='mp3',
		OutputS3BucketName=bucket,
		Text=updates[key],
		VoiceId=voice_id,
		TextType='ssml'
	)
	
	# We need task_id so we can track progress of task
	task_id = response['SynthesisTask']['TaskId']
	
	# Ping Polly every 5 secs, to see if MP3 is done
	finished = False
	while not finished:
		time.sleep(5)
		print("Getting " + key + "...")
		response = polly.get_speech_synthesis_task(TaskId=task_id)
		status = response['SynthesisTask']['TaskStatus']
		if status == 'completed' or status == 'failed':
			finished = True
	
	# data for Megaphone post call to create 
	data = {
		"targets": [{"id": podcast_guid, "type": "podcast"}],
		"title": "Covid report for " + key + " " + date,
		"region": "all",
		"position": 1,
		"priority": 1,
		"flightTimezone": "Eastern Time (US & Canada)",
		"geotargets": zips[key],
		"startAt": start,
		"endAt": end
	}
	
	headers = {'Content-Type': 'application/json', 'Authorization': 'Token token="' + token + '"'}
	
	r = requests.post(promo_url, headers=headers, json=data)
	content = json.loads(r.content)
	
	# Now we can create the "ad" inside the promo (i.e., the MP3 pre-roll)
	ad_url = "https://cms.megaphone.fm/api/organizations/" + org_guid + "/promos/" + content['id'] + "/advertisements"

	data = {
		"position": 1,
		"backgroundAudioFileUrl": "https://s3.amazonaws.com/" + bucket + "/" + task_id + ".mp3",
		"insertionPoint": "pre"
	}

	r = requests.post(ad_url, headers=headers, json=data)
	
	# clean up your mess
	s3.delete_object(Bucket='polly.wbur.org', Key=task_id + '.mp3')
	
	print("Finished " + key)