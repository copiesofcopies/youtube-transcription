import re
import time
import yaml
import json
import urllib
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

video_id_regex = re.compile('http://gdata.youtube.com/feeds/api/videos/(\w+)</ns0:id>')

def upload_video(filename, metadata):
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

    # set the path for the video file binary
    video_file_location = filename

    video_entry = gdata.youtube.YouTubeVideoEntry(media=media_group)

    # assuming that video_file_location points to a valid path
    new_entry = yt_service.InsertVideoEntry(video_entry, video_file_location)
    
    return new_entry


def get_video_from_url(url):
    (filename, headers) = urllib.urlretrieve(url)
    return filename


def get_entry_id(entry_id):
    m = video_id_regex.search(str(entry_id))
    if m:
        parsed_id = m.group(1)
        return parsed_id

    return False


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


if __name__ == "__main__":
    # Set up the command line argument parser
    parser = optparse.OptionParser()

    parser.add_option('-i', '--input-file',
                      action="store", dest="input_file",
                      help="""Input json file""",
                      default="")

    parser.add_option('-o', '--output-file',
                      action="store", dest="output_file",
                      help="""Output json file (with YouTube IDs)""",
                      default="")
    
    options, args = parser.parse_args()

    # Parse the json videos file
    videos_file = open(options.input_file, 'r')
    videos = json.load(videos_file)

    uploaded_ids = []

    for video in videos:
        fn = get_video_from_url(video)

        metadata = parse_metadata(videos[video])
        uploaded_vid = upload_video(fn, metadata)

        video_id = get_entry_id(uploaded_vid.id)

        videos[video]['id'] = video_id

    output_file = open(options.output_file, "wt")
    output_file.write(json.dumps(videos))
    output_file.close()
