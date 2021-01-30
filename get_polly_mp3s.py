import boto3
import time

# BOTO3 S3 docs
# https://boto3.amazonaws.com/v1/documentation/api/1.9.42/reference/services/s3.html#S3.Client.copy

# BOTO3 Polly docs
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/polly.html

aws_polly_profile_name = 'FILL THIS OUT' # An AWS profile name, with proper Polly and S3 perms

session = boto3.Session(profile_name=aws_polly_profile_name)
polly = session.client('polly')
s3 = session.client('s3')

title = "FILL THIS OUT! Needs a title"

# We like Matthew, but there are many more to choose from
# See: https://docs.aws.amazon.com/polly/latest/dg/voicelist.html
voice_id = 'Matthew'
sample_rate = '24000'
bucket = 'FILL THIS OUT' # publicly readable S3 bucket

# Text for MP3
# domain name='news' means it will use the "newscaster" style
# https://docs.aws.amazon.com/polly/latest/dg/using-newscaster.html
text ="""<speak> 
<amazon:domain name='news'>
	Insert you text!
</amazon:domain> 
</speak>"""

response = polly.start_speech_synthesis_task(
	Engine= 'neural', # need this for newscaster style
	OutputFormat='mp3',
	OutputS3BucketName=bucket,
	TextType="ssml",
	SampleRate=sample_rate,
	Text=text,
	VoiceId=voice_id
)

# We need task_id so we can track progress of task
task_id = response['SynthesisTask']['TaskId']

# Ping Polly every 5 secs, to see if MP3 is done
finished = False
while not finished:
	time.sleep(5)
	print("Getting " + title + "...")
	response = polly.get_speech_synthesis_task(TaskId=task_id)
	status = response['SynthesisTask']['TaskStatus']
	if status == 'completed':
		# When done get local copy of file, then delete
		s3.download_file(bucket, task_id + '.mp3', title + '_' + voice_id + '.mp3')
		s3.delete_object(Bucket=bucket, Key=task_id+'.mp3')
		finished = True
		print ("Done")
	if status == 'failed':
		finished = True