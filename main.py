import auth
import requests
import pandas as pd
from datetime import datetime, timedelta

## Initialize twitter api with credentials from auth.py
api = auth.twitter_api()

## NOC Database API
global base_url
base_url = "https://health-products.canada.ca/api/notice-of-compliance/"
sub_url = "noticeofcompliancemain/?type=json&lang=en"
noc_api = requests.get(base_url+sub_url).json()
print("Found {} NOCs".format(len(noc_api)))
## Create a list of tweet messages to identify any dupes
global dupe
dupe=[]
for tweets in api.user_timeline():
	dupe.append(tweets.text)

## Main tweeting function

def tweet(single_noc): ## x: iteration, new_nocs: data
	global dupe
	global base_url
	noc_no = str(single_noc['noc_number'])
	lang="en"
	dp_url = base_url + "drugproduct/?lang=" + lang + "&type=json&id=" + noc_no
	dp_api = requests.get(dp_url).json()
	try:
		print("Attempting to compile message for {}".format(dp_api[0]['noc_br_brandname']))
	except:
		print(single_noc['noc_number'])
	if single_noc["noc_on_submission_type"] == "New Drug Submission (NDS)":
		msg = "New drug approved for " + dp_api[0]["noc_br_brandname"] + " by " + single_noc["noc_manufacturer_name"] + " #NewNOCAlert #HCApproves"
		if msg not in dupe: #Only tweet if unique tweet
			try:
				api.update_status(msg)
				print(msg)
			except tweepy.TweepError as e:
				print(e)
		else:
			print("msg already tweeted - '{}'".format(msg))
	elif single_noc["noc_on_submission_type"] == "Abbreviated New Drug Submission (ANDS)":
		msg = "New generic drug approved for " + dp_api[0]["noc_br_brandname"] + " by " + single_noc["noc_manufacturer_name"] + " #NewNOCAlert #HCApproves"
		if msg not in dupe:
			try:
				api.update_status(msg)
				print(msg)
			except tweepy.TweepError as e:
				print(e)
		else:
			print("msg already tweeted - '{}'".format(msg))
	else:
		print("Not a (A)NDS")


## Create dataframe from noc api

df = pd.DataFrame.from_dict(noc_api)
df['noc_date'] = pd.to_datetime(df['noc_date']) # conver to datetime format
max_date = max(df['noc_date'])
print("Last issued NOC date: ", max_date)
df = df[(datetime.today() - timedelta(days=4)) < df.noc_date] # filter dataframe for only NOCs posted in last 3 days
df = df[df['noc_submission_class'] != "Admin"]
df = df[(df['noc_on_submission_type'] == "Abbreviated New Drug Submission (ANDS)") | (df['noc_on_submission_type'] == "New Drug Submission (NDS)")]

if df.shape[0]==0:
	print("No new NOC on {}".format(datetime.today()))
else:
	df.apply(lambda x: tweet(x), axis=1)
