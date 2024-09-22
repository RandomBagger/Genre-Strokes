import json
import os
import random
from flask import Flask, render_template, render_template_string, redirect, request
import cloudinary
import cloudinary.api
import cloudinary.uploader

CONFIG_FILE = "./config.json"
GAMEDATAJSON_FILEPATH = "./game-data.json"
MEDIASOURCE_PATH = os.path.join("static", "mediaSource", "nsfw")
NUMBER_OF_OPTIONS = 4  # How many options should be given to the player
NO_CONSEQUENCES_TRY_NUMBER = 8  # How many tries before the screen starts fading
HARDEST_SCORE_LIMIT = 25  # Score that will be the hardest to get
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB allowed upload size to Cloudinary


def load_config():
    """Load config from file or prompt for CLOUDINARY_URL and create config file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as config_file:
            config_data = json.load(config_file)
        return config_data
    else:
        # If config file doesn't exist, prompt for CLOUDINARY_URL
        cloudinary_url = input("Enter your CLOUDINARY_URL (format: cloudinary://<api_key>:<api_secret>@<cloud_name>): ")

        # Parse CLOUDINARY_URL
        if not cloudinary_url.startswith("cloudinary://"):
            raise ValueError("Invalid CLOUDINARY_URL format.")
        
        cloudinary_parts = cloudinary_url.replace("cloudinary://", "").split("@")
        credentials, cloud_name = cloudinary_parts
        api_key, api_secret = credentials.split(":")

        # Create a config dictionary
        config_data = {
            "cloud_name": cloud_name,
            "api_key": api_key,
            "api_secret": api_secret
        }

        # Write the config file
        with open(CONFIG_FILE, 'w') as config_file:
            json.dump(config_data, config_file)

        return config_data


# Load Cloudinary credentials from config
config = load_config()

# Cloudinary configuration
cloudinary.config(
    cloud_name=config["cloud_name"],
    api_key=config["api_key"],
    api_secret=config["api_secret"]
)

global score, playing
score: int = 0
playing: bool = False

def tags_input_formatter(data):
    data = json.loads(data)
    return data

def source_provider():
    '''Give a random Url of a image in database'''
    data = get_game_data()["NSFW"]
    length_of_data = len(data)


    return data[random.randrange(length_of_data)]

def extension_of(filename:str) -> str:
    return filename.split('.')[-1].lower()


def post_game_data(MEGA_DATA:dict) -> None:
    '''Don't forget to enclose the game data in a tagged dictionary '''
    with open(GAMEDATAJSON_FILEPATH,'w') as gamedata_file:
        json.dump(MEGA_DATA,gamedata_file)


def get_game_data() -> dict:
    with open(GAMEDATAJSON_FILEPATH,'r') as gamedata_file:
        gamedata = gamedata_file.read()
        gamedata2 = json.loads(gamedata)

    return gamedata2


def get_media_folder_data():
    media = os.listdir(MEDIASOURCE_PATH)

    temp = list()
    temp2 = list()
    for value in media:
        file_path = os.path.join(MEDIASOURCE_PATH, value)
        if extension_of(value) == 'url':
            with open(file_path) as file:
                data = file.read().split('\n')# separates newline
                for dt in data:
                    temp2.extend(dt.split(',')) #separates comma separated value

                data = [dt for dt in temp2 if dt != ''] #Removes white spaces

            temp.extend(data)
            continue
        elif extension_of(value) in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg','mp4', 'webm', 'ogv', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'mpeg', 'mpg']:
            temp.append(file_path)
    media = temp
    return media


def get_cloudinary_images():
    """Retrieve URLs of all images stored in Cloudinary"""
    try:
        # Fetch the list of resources
        response = cloudinary.api.resources(type='upload', resource_type='image', max_results=500)
        images = response['resources']

        # List to store image URLs
        image_urls = []

        for image in images:
            image_urls.append(image['url'])

        # Handle pagination if more images are present
        while 'next_cursor' in response:
            response = cloudinary.api.resources(type='upload', resource_type='image', max_results=500, next_cursor=response['next_cursor'])
            images = response['resources']
            for image in images:
                image_urls.append(image['url'])

        return image_urls

    except Exception as e:
        print(f"An error occurred: {e}")
        return []



app = Flask(__name__)

@app.route('/')
def home():
    return redirect('/game')


@app.route('/game')
def game():
    global score , playing
    gameData = dict()

    try:
        res = source_provider()
    except Exception as err:

        if str(err) == "empty range for randrange()":
            return redirect("/pullForm")
        
        return str(err)
    
    all_tags = list(set(get_game_data()["MEGA_TAG_LIST"]))

    # Prevents infinity while loop due to low tags 
    if len(all_tags) < 5:
        # Just add more tags in game-data.json
        return "{This is a Error}\n(There wasn't enough tags to start the game)(To solve this issue contact the admins)"

    gameData["score"] = score
    if score > NO_CONSEQUENCES_TRY_NUMBER:
        '''
        0.03 was the hardest value to see
        (HARDEST_SCORE_LIMIT - NO_CONSEQUENCES_TRY_NUMBER) because we started after no consq try no.
        score-NO_CONSEQUENCES_TRY_NUMBER to give a linear feel of difficulty
        '''
        gameData["opacity"] = (0.03 * (HARDEST_SCORE_LIMIT - NO_CONSEQUENCES_TRY_NUMBER)) / (score-NO_CONSEQUENCES_TRY_NUMBER)
                               
    gameData["URL"] = res["URL"]

    gameData["OPTIONS"] = list()
    len_res_tags = len(res["TAGS"])

    # To handle null tags 
    if len_res_tags > 0:
        gameData["OPTIONS"].append(
            str(res["TAGS"][random.randrange(len_res_tags)])
            ) #ANSWER


    option_counter = len(gameData["OPTIONS"]) #To handle null correct answer
    while option_counter < (NUMBER_OF_OPTIONS) :
        value = all_tags[random.randrange(len(all_tags))]
        if value in gameData["OPTIONS"]:
            continue
        gameData["OPTIONS"].append(str(value)) # Here it is str to avoid any int to go through

        option_counter += 1

    gameData["OPTIONS"] = random.sample(gameData["OPTIONS"], len(gameData["OPTIONS"])) #Shuffling the list


    gameData["TAG_LIST"] = res["TAGS"]
    gameData["playing"] = playing
    gameData["SCORE"] = score

    return render_template("root.html", data = gameData)

@app.route('/answerme', methods=["POST"])
def answer_me():
    global score, playing
    game_overData = dict()
    option = request.form.get("option_value")
    tag_list = request.form.get("tag_list")
    url = request.form.get("URL")

    if option not in tag_list:
        #wrong answer
        playing = False
        game_overData["SCORE"] = score
        game_overData["URL"] = url


        score = 0
        return render_template('game_over.html',data=game_overData)
    
    playing = True
    score += 1
    return redirect('/game')


@app.route('/pullForm')
def pullForm():
    formData = dict()
    existing_url_list = list()
    game_data = get_game_data()

    for i in range(len(game_data["NSFW"])):
        existing_url_list.append(game_data["NSFW"][i]["URL"]) #This filters already tagged links

    media = get_media_folder_data()
    media.extend(get_cloudinary_images())
    

    image_list = [value for value in media if value not in existing_url_list]

    if image_list == []:
        return redirect('/')

    image_url = image_list[random.randrange(len(image_list))]
    formData["URL"] = image_url
    formData["Tag_list"] = game_data["MEGA_TAG_LIST"]

    print(formData)
    return render_template("pullForm.html",data=formData)

@app.route('/submit-tags', methods = ["POST"])
def submit_tags():
    single_img_data = dict()
    MEGA_DATA = dict()

    selected_options:list = request.form.getlist('option')
    
    img_url = request.form.get("image_url")
    more_tags = request.form.get("additional_tags").lower().split(',')
    more_tags = [i.strip() for i in more_tags]#Removes spaces from entries
    more_tags = [i for i in more_tags if i != '']#Removes empty entries

    if not selected_options and not more_tags:
        return redirect('/pullForm')

    tags = selected_options
    tags.extend(more_tags)#Adding the additional tags
    tags = list(set(tags))#Removing duplicates

    game_data = get_game_data()

    single_img_data["URL"] = img_url
    single_img_data["TAGS"] = tags

    game_data["NSFW"].append(single_img_data)

    if more_tags:
        game_data["MEGA_TAG_LIST"].extend(more_tags)#Adds the additional tags to the mega list

    #Removing duplicate entries
    game_data["MEGA_TAG_LIST"] = list(set(game_data["MEGA_TAG_LIST"]))

    post_game_data(game_data)
    return redirect('/pullForm')


@app.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return 'No file part', 400
    
    files = request.files.getlist('files')
    
    if not files:
        return 'No files selected', 400
    
    urls = []
    errors = []

    for file in files:
        if file.filename == '':
            errors.append('No selected file')
            continue
        
        # Check file size
        file.seek(0, os.SEEK_END)  # Move the cursor to the end of the file to get the size
        file_size = file.tell()
        file.seek(0)  # Reset the cursor to the beginning of the file
        
        if file_size > MAX_FILE_SIZE:
            # Save large files locally
            try:
                file_path = os.path.join(MEDIASOURCE_PATH, file.filename)
                file.save(file_path)
                errors.append(f'The file {file.filename} exceeds the 10MB size limit and was saved locally.')
            except Exception as e:
                errors.append(f'Error saving file {file.filename} locally: {e}')
            continue
        
        if file:
            try:
                # Upload to Cloudinary
                response = cloudinary.uploader.upload(file)
                url = response['secure_url']
                urls.append(url)
            except Exception as e:
                errors.append(f'Error uploading file {file.filename}: {e}')

    # Construct the response
    response_html = '<h1>Files uploaded successfully!</h1>'
    
    if urls:
        response_html += '<ul>'
        for url in urls:
            response_html += f'<li><a href="{url}" target="_blank">View File</a></li>'
        response_html += '</ul>'
    
    if errors:
        response_html += '<h2>Errors:</h2><ul>'
        for error in errors:
            response_html += f'<li>{error}</li>'
        response_html += '</ul>'

    return render_template_string(response_html)

@app.route('/upload-form')
def upload_form():
    return render_template("upload_form.html")



if __name__ == '__main__':
    app.run(host='0.0.0.0')

