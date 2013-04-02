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
import yaml
import json
import optparse
import logging
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

# Connect to the YouTube API
yt_service.ProgrammaticLogin()


# Retrieve a single caption track given its URL
def get_caption_track(url):
    return yt_service.Get("%s" % url, converter=converter)


# This seemingly useless function has to be passed into
# yt_service.Get() to "process" the caption track because of a WONTFIX
# bug <https://code.google.com/p/gdata-issues/issues/detail?id=4289>
# in Google's gdata library.
def converter(url):
    return url


# Get a GDataFeed of all the caption tracks associated with the video
def get_available_caption_tracks(id):
    caption_feed = yt_service.Get('https://gdata.youtube.com/feeds/api/videos/%s/captions' % id)

    return caption_feed


if __name__ == "__main__":
    # Set up the command line argument parser
    # TODO: check for required -i and -o parameters, exit if missing
    parser = optparse.OptionParser()

    parser.add_option('-i', '--input-file', action="store", dest="input_file",
                      help="""Input manifest file (JSON)""", default="")

    parser.add_option('-o', '--output-dir', action="store", dest="output_dir",
                      help="""Directory to save transcriptions in (optional; omit 
                              or enter '-' to print to standard output)""",
                      default="-")

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

    # Open and parse the json video manifest
    with open(options.input_file, 'r') as f:  
        videos = json.load(f)

    # For each video, get the caption tracks and store them locally
    for video in videos:
        video_id = videos[video]['id']

        logging.info("Retrieving caption tracks for video with ID %s..." % video_id)
        feed = get_available_caption_tracks(video_id)
    
        inc = 0

        for entry in feed.entry:
            caption_track = get_caption_track(entry.content.src)
            
            # If there's more than one caption track, increment
            # filenames. TODO: get more meaningful information about
            # the differences between tracks and append more helpful
            # distinguishing info.
            
            if inc > 0:
                fn = "%s-%s" % (video_id, inc)
            else:
                fn = "%s" % video_id

            if options.output_dir == '-':
                print "# caption-track [%s] (%s)" % (fn, videos[video]['title'])
                print caption_track
            else:
                output_path = os.path.normpath(options.output_dir) + os.sep + fn + ".sbv"
                    
                logging.info("Saving caption track to %s" % (output_path))

                with open(output_path, "wt") as caption_file:
                    caption_file.write(caption_track)
