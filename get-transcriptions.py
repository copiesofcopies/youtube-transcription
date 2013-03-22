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

import yaml
import json
import optparse
import gdata.youtube
import gdata.youtube.service

yt_service = gdata.youtube.service.YouTubeService()

# Turn on HTTPS/SSL access.
# Note: SSL is not available at this time for uploads.
yt_service.ssl = True

# Parse the yaml config file
config_file = open('config.yaml', 'r')
config = yaml.load(config_file.read())

# A complete client login request
yt_service.email = config['user_email']
yt_service.password = config['user_password']
yt_service.source = config['source']
yt_service.developer_key = config['developer_key']
yt_service.client_id = config['client_id']
yt_service.ProgrammaticLogin()


def get_caption_track(url):
    return yt_service.Get("%s" % url, converter=converter)


def converter(url):
    return url


def get_available_caption_tracks(id):
    caption_feed = yt_service.Get('https://gdata.youtube.com/feeds/api/videos/%s/captions' % id)

    return caption_feed


if __name__ == "__main__":
    # Set up the command line argument parser
    parser = optparse.OptionParser()

    parser.add_option('-i', '--input-file',
                      action="store", dest="input_file",
                      help="""Input json file""",
                      default="")

    parser.add_option('-o', '--output-dir',
                      action="store", dest="output_dir",
                      help="""Output directory""",
                      default="")
    
    options, args = parser.parse_args()

    videos_file = open(options.input_file, 'r')
    videos = json.load(videos_file)

    for video in videos:
        video_id = videos[video]['id']
        print "Getting available caption tracks for %s" % video_id
        feed = get_available_caption_tracks(video_id)
    
        inc = 0

        for entry in feed.entry:
            caption_track = get_caption_track(entry.content.src)
            
            if inc > 0:
                fn = "%s-%s.txt" % (video_id, inc)
            else:
                fn = "%s.txt" % video_id

            caption_file = open("%s%s" % (options.output_dir, fn), "wt")
            caption_file.write(caption_track)
            caption_file.close()
