youtube-transcription
=====================

Scripts to retrieve videos, upload them to YouTube, and retrieve the automatically-generated transcriptions. Requires you to first [register](https://developers.google.com/youtube/registering_an_application) a YouTube Data API-consuming application with Google.

## config.yaml

The scripts require a files called config.yaml (formatted like the included file config.yaml.example) containing your YouTube auth information.

## upload-videos.py

Accepts a json manifest with video URLs and metadata values. Retrieves the videos, uploads them to YouTube, and outputs a modified manifest including YouTube IDs.

Parameters (both required):

* -i --input-file: the full path of the json manifest
* -o --output-file: the full path of the modified manifest

## get-transcriptions.py

Accepts the modified manifest produced by upload-videos.py. Retrieves all transcripts associated with the videos and stores them in the supplied output directory.

Parameters (both required):

* -i --input-file: the full path of the json manifest
* -o --output-dir: the path of the directory in which to store the transcripts

## Format for input manifest (json):

```
{
"http://example.org/video.mp4": {
  "title": "Title",
  "category_term": "Film",
  "category_label": "Film &amp; Animation",
  "keywords": "some, useful, keywords",
  "description": "A nice description"
  }
}
```
