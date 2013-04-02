# Copyright 2013 Aaron Williamson <aaron@copiesofcopies.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import sys
import yaml
import json
import urllib
import logging
import optparse
import gdata.youtube
import gdata.youtube.service

yt_service = gdata.youtube.service.YouTubeService()

# Turn on HTTPS/SSL access.
# Note: SSL is not available at this time for uploads.
yt_service.ssl = True

# Parse the yaml config file
with open('config.yaml', 'r') as config_file:
    config = yaml.load(config_file.read())

# A complete client login request
yt_service.email = config['user_email']
yt_service.password = config['user_password']
yt_service.source = config['source']
yt_service.developer_key = config['developer_key']
yt_service.client_id = config['client_id']
yt_service.ProgrammaticLogin()

# Regex to extract video ID from uploaded video object. (Why there's
# no useful "ID" field is beyond me.)
video_id_regex = re.compile('http://gdata.youtube.com/feeds/api/videos/(\w+)</ns0:id>')

# Initialize options global
options = None

# Upload a video to YouTube and get back a YouTubeVideoEntry object
def upload_video(filename, metadata):
    # Create a container object for video metadata
    media_group = gdata.media.Group(
        title=gdata.media.Title(text=metadata['title']),
        description=gdata.media.Description(description_type='plain',
                                            text=metadata['description']),
        keywords=gdata.media.Keywords(text=metadata['keywords']),
        category=gdata.media.Category(
                text=metadata['category_term'],
                scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
                label=metadata['category_label']),
        player=None,
        private=gdata.media.Private()
        )

    # Create a YouTubeVideoEntry with the metadata associated
    video_entry = gdata.youtube.YouTubeVideoEntry(media=media_group)

    # Upload the video at `filename` and associate it with the new
    # YouTubeVideoEntry
    new_entry = yt_service.InsertVideoEntry(video_entry, filename)
    
    return new_entry


# Download the video at a given URL
# TODO: handle missing or unavailable videos
def get_video_from_url(url):
    if options.quiet: 
        reporthook = None
    else:
        reporthook = download_progress

    (filename, headers) = urllib.urlretrieve(url, reporthook=reporthook)

    if not options.quiet: sys.stdout.write("\n")

    return filename


# Extract a video's YT ID from its full URL
def get_entry_id(entry_url):
    m = video_id_regex.search(str(entry_url))
    if m:
        parsed_id = m.group(1)
        return parsed_id

    return False


# Map provided metadata to dict to be passed with new video (ensures
# empty strings are passed instead of None values)
def parse_metadata(metadata):
    all_metadata = {
        'local_id': '',
        'title': '',
        'description': '',
        'keywords': '',
        'category_term': '',
        'category_label': ''
        }

    for k in all_metadata:
        all_metadata[k] = metadata.get(k, '')

    return all_metadata


# Print file download progress to stdout
def download_progress(count, blockSize, totalSize):
    percent = int(count*blockSize*100/totalSize)
    sys.stdout.write("\rProgress: %d%%" % percent)
    sys.stdout.flush()


if __name__ == "__main__":
    # Set up the command line argument parser
    # TODO: check for required -i and -o parameters, exit if missing
    parser = optparse.OptionParser()

    parser.add_option('-i', '--input-file', action="store", dest="input_file",
                      help="""Input manifest file (JSON)""", default="")

    parser.add_option('-o', '--output-file', action="store", dest="output_file",
                      help="""Output manifest file (optional; omit to save to 
                              input file)""",
                      default="")

    parser.add_option('-q', '--quiet', action='store_true', dest='quiet',
                      help="""Suppress informational messages""", 
                      default=False)

    options, args = parser.parse_args()

    if options.input_file == '':
        parser.print_help()
        exit(-1)

    # Set logging level
    if options.quiet:
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    # Parse the json videos file
    with open(options.input_file, 'r') as f:  
        videos = json.load(f)

    uploaded_ids = []

    for video in videos:
        # Download the video indicated by the URL
        logging.info("Downloading video from %s..." % video)
        fn = get_video_from_url(video)

        # Fill in the video metadata values
        metadata = parse_metadata(videos[video])

        logging.info("Uploading video from %s to YouTube..." % video)
        # Upload the video
        uploaded_vid = upload_video(fn, metadata)

        # Grab the YouTube ID and store it with the metadata
        video_id = get_entry_id(uploaded_vid.id)
        videos[video]['id'] = video_id

        # Remove the local file
        os.remove(fn)

        logging.info("Finished uploading; YouTube ID is %s" % video_id)

    # Write a json file identical to the input, except with the YT id
    # added for each entry
    if options.output_file:
        output_fn = options.output_file
    else:
        output_fn = options.input_file

    with open(output_fn, "wt") as output_file:
        output_file.write(json.dumps(videos, indent=4, sort_keys=True))
