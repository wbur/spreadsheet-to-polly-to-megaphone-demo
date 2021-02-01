# Make Your Spreadsheet Talk!

## Before You Start

This is in instructional demo of how WBUR automated the creation of town-specific COVID data pre-rolls for it short-form COVID news podcast.

As such, it is a very niche example. It uses specific services (Polly, Megaphone) that you might not have or use. This is *not* your typical README.

That being said, it can hopefully inform and inspire you to turn normalized data into audio. If you already have an audio hosting service, a text-to-speech service, and some coding chops, you're on your way! It's surprisingly easy and affordable.

## Digging In

`create_covid_promos.py` is the file you want to focus on.

1. It starts by iterating over a (sample, single-row) CSV file, each row representing a town in Massachusetts.
2. It picks out the data we want to use, massage it a little, insert it into a template.
3. The resulting script is sent to Polly, the AWS text-to-speech service.
4. It waits until the process is complete.
5. Then it gathers all the necessary data — incuding the zip codes that match to a given town — and uses Megaphone's API to create a Promo, which is basically a container for all the data for the pre-roll.
6. Finally, it uses the API again to create an ad — the actual pre-roll — by grabbing the MP3 from S3.

## Bonus for Shopping

Also included is `get_polly_mp3s.py` which is a quick and dirty way to create MP3s from text via Polly and S3.

## Good Luck!

Once again, this repo should just be used as a template/inspiration. Feel free to use any/all parts of the code. If you already use AWS and Megaphone, that will of course help, but you'll still need all the proper keys and profiles, a familiarity with AWS CLI, Megaphone promos, etc. This is *not* a plug-and-play repo.
