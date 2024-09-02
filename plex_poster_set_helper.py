import requests
import math
import sys
import os
import urllib.request
import stat
import os.path
import json
from bs4 import BeautifulSoup
from plexapi.server import PlexServer
import plexapi.exceptions
import time
import re
import xml.etree.ElementTree as ET

LABEL_RATING_KEYS = {}
MEDIA_TYPES_PARENT_VALUES = {
    "movie": 1,
    "show": 2,
    "season": 2,
    "episode": 2,
    "album": 9,
    "track": 9,
}

# Define global variables
tv = []
movies = []
collections = []
append_label = "Overlay"
overwrite_labelled_shows = False
assets_directory = "assets"
overwrite_assets = False
base_url = ""
token = ""
asset_folders = True
only_process_new_assets = True
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def plex_setup():
    global tv, movies, collections, append_label, overwrite_labelled_shows, assets_directory, overwrite_assets, base_url, token, asset_folders, only_process_new_assets, useragent

    if os.path.exists("config.json"):
        try:
            config = json.load(open("config.json"))
            base_url = config.get("base_url", "").rstrip('/')
            token = config.get("token", "")
            tv_library = config.get("tv_library", [])
            movie_library = config.get("movie_library", [])
            append_label = config.get("append_label", "Overlay")
            assets_directory = config.get("assets_directory", "assets")
            overwrite_assets = config.get("overwrite_assets", False)
            overwrite_labelled_shows = config.get("overwrite_labelled_shows", False)
            asset_folders = config.get("asset_folders", True)  # Default to True if not specified
            asset_folders = config.get("only_process_new_assets", True)  # Default to True if not specified
            useragent = config.get("useragent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")  # Default if not specified

        except (FileNotFoundError, json.JSONDecodeError) as e:
            sys.exit(f"Error with config.json file: {e}. Please consult the readme.md.")
        except Exception as e:
            sys.exit(f"An unexpected error occurred: {e}. Please consult the readme.md.")
        
        try:
            plex = PlexServer(base_url, token)
        except requests.exceptions.RequestException:
            sys.exit('Unable to connect to Plex server. Please check the "base_url" in config.json, and consult the readme.md.')
        except plexapi.exceptions.Unauthorized:
            sys.exit('Invalid Plex token. Please check the "token" in config.json, and consult the readme.md.')
        
        if isinstance(tv_library, str):
            tv_library = [tv_library]
        elif not isinstance(tv_library, list):
            sys.exit("tv_library must be either a string or a list")
        
        for tv_lib in tv_library:
            try:
                plex_tv = plex.library.section(tv_lib)
                tv.append(plex_tv)
            except plexapi.exceptions.NotFound:
                sys.exit(f'TV library named "{tv_lib}" not found. Please check the "tv_library" in config.json, and consult the readme.md.')        
        
        if isinstance(movie_library, str):
            movie_library = [movie_library]
        elif not isinstance(movie_library, list):
            sys.exit("movie_library must be either a string or a list")
        
        for movie_lib in movie_library:
            try:
                plex_movie = plex.library.section(movie_lib)
                movies.append(plex_movie)
            except plexapi.exceptions.NotFound:
                sys.exit(f'Movie library named "{movie_lib}" not found. Please check the "movie_library" in config.json, and consult the readme.md.')

    else:
        sys.exit("No config.json file found. Please consult the readme.md.")


def cook_soup(url):  
    headers = { 
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', 'Sec-Ch-Ua-Mobile': '?0', 'Sec-Ch-Ua-Platform': 'Windows' 
            }

    response = requests.get(url, headers=headers)

    if response.status_code == 200 or (response.status_code == 500 and "mediux.pro" in url):
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        sys.exit(f"Failed to retrieve the page. Status code: {response.status_code}")    
        
def get_asset_file_path(assets_directory, plex_folder, file_name):
    # Construct the path for the Plex folder within the assets directory
    plex_folder_path = os.path.join(assets_directory, plex_folder)
    
    # Construct the full path for the file
    return os.path.join(plex_folder_path, file_name)

def ensure_directory(directory_path):
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path, mode=0o755)
            print(f"Directory created: {directory_path}")
        except Exception as e:
            print(f"Failed to create directory: {e}")

def save_to_assets_directory(assets_directory, plex_folder, file_name, file_url):
    file_path = get_asset_file_path(assets_directory, plex_folder, file_name)

    # Check if file already exists and if overwriting is allowed
    if os.path.exists(file_path):
        if not overwrite_assets:
            print(f"File already exists and overwriting is disabled: {file_path}")
            return file_path
        else:
            print(f"Overwriting existing file: {file_path}")
    
    # Create the Plex folder path if it doesn't exist
    plex_folder_path = os.path.dirname(file_path)
    if not os.path.exists(plex_folder_path):
        os.makedirs(plex_folder_path)
        print(f"Directory created: {plex_folder_path}")
    
    # Define headers
    headers = {
        "User-Agent": f"{useragent}"
    }
    
    # Download and save the file
    try:
        # Use requests to download the file from the provided URL
        response = requests.get(file_url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"File downloaded and saved to: {file_path}")
            return file_path
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to save file to assets directory: {e}")
        return None

def title_cleaner(string):
    if " (" in string:
        title = string.split(" (")[0]
    elif " -" in string:
        title = string.split(" -")[0]
    else:
        title = string

    title = title.strip()

    return title


def parse_string_to_dict(input_string):
    # Remove unnecessary replacements
    input_string = input_string.replace('\\\\\\\"', "")
    input_string = input_string.replace("\\","")
    input_string = input_string.replace("u0026", "&")

    # Find JSON data in the input string
    json_start_index = input_string.find('{')
    json_end_index = input_string.rfind('}')
    json_data = input_string[json_start_index:json_end_index+1]

    # Parse JSON data into a dictionary
    parsed_dict = json.loads(json_data)
    return parsed_dict

def add_label_rating_key(library_item):
    existing_section = LABEL_RATING_KEYS.get(library_item.librarySectionID, {})

    if append_label and append_label not in library_item.labels:
        existing_keys = existing_section.get("keys", [])

        if str(library_item.ratingKey) not in existing_keys:
            existing_keys += [str(library_item.ratingKey)]

        existing_type = existing_section.get(
            "type", MEDIA_TYPES_PARENT_VALUES[library_item.type]
        )

        LABEL_RATING_KEYS[library_item.librarySectionID] = {
            "keys": existing_keys,
            "type": existing_type,
        }


def get_file_path_from_plex(rating_key):
    headers = {'X-Plex-Token': token}
    response = requests.get(f"{base_url}/library/metadata/{rating_key}", headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get metadata: {response.status_code}")

    # Parse the XML response
    try:
        root = ET.fromstring(response.text)
        location_element = root.find(".//Location")
        
        if location_element is not None:
            file_path = location_element.get('path')
            
            if file_path:
                # Get the last folder from the file path
                last_folder = os.path.basename(file_path)
                return last_folder
            else:
                raise Exception("Path attribute not found in Location element")
        else:
            location_element = root.find(".//Part")
            if location_element is not None:
                file_path = location_element.get('file')
                if file_path:
                    # Get the last folder from the file path
                    dir_path = os.path.dirname(file_path)
                    last_folder = os.path.basename(dir_path)
                    return last_folder
                else:
                    raise Exception("Path attribute not found in Location element")
            else:
                raise Exception("Location element not found in XML")
    
    except ET.ParseError as e:
        raise Exception(f"Failed to parse XML: {e}")


def find_in_library(library, poster):
    for lib in library:
        try:
            if poster["year"] is not None:
                library_item = lib.get(poster["title"], year=poster["year"])
            else:
                library_item = lib.get(poster["title"])
            
            if library_item:
                add_label_rating_key(library_item)
                rating_key = library_item.ratingKey
                # Get the file path from Plex
                show_path = get_file_path_from_plex(rating_key)
                return library_item, show_path

        except Exception as e:
            # Convert the exception to a string for easy checking
            error_message = str(e)
            
            if "Unable to find item with title" in error_message:
                continue  # Skip printing this specific error
            else:
                print(e)  # Print all other errors

    return None, None



def find_collection(library, poster):
    collections = []
    for lib in library:
        try:
            movie_collections = lib.collections()
            for plex_collection in movie_collections:
                if plex_collection.title == poster["title"]:
                    collections.append(plex_collection)
        except:
            pass

    if collections:
        return collections

    return None

        
def update_plex_labels():
    headers = {"X-Plex-Token": token}

    if LABEL_RATING_KEYS:
        for section_id, item in LABEL_RATING_KEYS.items():
            # Loop through each rating key to update labels for each show
            for rating_key in item["keys"]:
                label_exists = check_label_for_item(rating_key)
                if not label_exists:
                    # Construct the URL to update labels for a specific item
                    url = f"{base_url}/library/metadata/{rating_key}".format(
                        rating_key=rating_key
                    )

                    params = {
                        "label.locked": 1,  # Locks the label so it can't be auto-removed
                        "label[0].tag.tag": append_label,  # The label to append
                    }

                    # Perform the PUT request to update labels with timeout
                    try:
                        r = requests.put(url, headers=headers, params=params, timeout=10)

                        if r.status_code == 200:
                            print(f"Label '{append_label}' applied successfully to show with rating key {rating_key}")
                        else:
                            print(f"Failed to apply label '{append_label}' to show with rating key {rating_key} - {r.status_code}: {r.reason}")
                    except requests.Timeout:
                        print(f"Request to show with rating key {rating_key} timed out.")
                    except requests.RequestException as e:
                        print(f"An error occurred while updating labels for show with rating key {rating_key}: {e}")


def check_label_for_item(rating_key):
    headers = {"X-Plex-Token": token}
    
    # Construct the URL to get metadata for a specific item
    url = f"{base_url}/library/metadata/{rating_key}"
    
    try:
        # Fetch metadata for the item
        r = requests.get(url, headers=headers, timeout=10)
        
        r.raise_for_status()  # Raise an error for bad responses
        
        # Parse XML response
        root = ET.fromstring(r.content)
        
        # Extract labels with specific tag attribute
        labels = [label.get('tag') for label in root.findall(".//Label")]
        
        # Check if the append_label is present in tags
        if append_label in labels:
            return True
        else:
            return False
            
    except requests.RequestException as e:
        print(f"An error occurred while checking label for item with rating key {rating_key}: {e}")
        return False
    except ET.ParseError as e:
        print(f"Failed to parse XML response for rating key {rating_key}: {e}")
        return False
                                        
def upload_tv_poster(poster, tv):
    tv_show, show_path = find_in_library(tv, poster)
    if tv_show is not None:
        if show_path is not None:
            # Check if label is present and overwrite is not allowed
            label_exists = check_label_for_item(tv_show.ratingKey)
            if label_exists and not overwrite_labelled_shows:
                print(f"Skipping upload for {show_path} as it already has the label '{append_label}'.")
                return
            season_str = str(poster['season']).zfill(2)
            episode_str = str(poster['episode']).zfill(2)

            # Define the file name based on poster type
            if asset_folders:
                # Exclude the poster['title'] prefix when asset_folders is True
                if poster["season"] == "Cover":  # cover art
                    file_name = f"poster.jpg"
                elif poster["season"] == "Backdrop":  # background art
                    file_name = f"background.jpg"
                elif poster["season"] >= 0:
                    if poster["episode"] == "Cover":
                        file_name = f"Season{season_str}.jpg"
                    elif poster["episode"] is None:
                        file_name = f"Season{season_str}.jpg"
                    elif poster["episode"] is not None:
                        file_name = f"S{season_str}E{episode_str}.jpg"
                else:
                    file_name = f"ERROR.jpg"  # Default file name if no other conditions match
            else:
                # Include the poster['title'] prefix when asset_folders is False
                if poster["season"] == "Cover":  # cover art
                    file_name = f"{show_path}.jpg"
                elif poster["season"] == "Backdrop":  # background art
                    file_name = f"{show_path}_background.jpg"
                elif poster["season"] >= 0:
                    if poster["episode"] == "Cover":
                        file_name = f"{show_path}_Season{season_str}.jpg"
                    elif poster["episode"] is None:
                        file_name = f"{show_path}_Season{season_str}.jpg"
                    elif poster["episode"] is not None:
                        file_name = f"{show_path}_S{season_str}E{episode_str}.jpg"
                
                else:
                    print(f"Skipping upload for {poster['url']} due to sorting error.")
                    return

            # Check if the file already exists in the assets directory
            if asset_folders:
                file_path = get_asset_file_path(assets_directory, f"tv/{show_path}", file_name)
            else:
                file_path = get_asset_file_path(assets_directory, f"tv", file_name)
            if os.path.exists(file_path) and not overwrite_assets:
                if only_process_new_assets:
                    print(f"Skipping upload for {poster['title']} as it already exists in {tv_show.librarySectionTitle} library.")
                    return
                else:
                    print(f"Using existing file for upload to {poster['title']} in {tv_show.librarySectionTitle} library.")
            else:
                # Save the file to the assets directory
                if asset_folders:
                    file_path = save_to_assets_directory(assets_directory, f"tv/{show_path}", file_name, poster['url'])
                else:
                    file_path = save_to_assets_directory(assets_directory, f"tv", file_name, poster['url'])
                if file_path is None:
                    print(f"Skipping upload for {show_path} {poster['title']} due to download error.")
                    return

            # Proceed with the upload logic as before
            try:
                if poster["season"] == "Cover":
                    upload_target = tv_show
                    print(f"Uploading cover art for {poster['title']} - {poster['season']} in {tv_show.librarySectionTitle} library.")
                elif poster["season"] == 0:
                    upload_target = tv_show.season("Specials")
                    print(f"Uploading art for {poster['title']} - Specials in {tv_show.librarySectionTitle} library.")
                elif poster["season"] == "Backdrop":
                    upload_target = tv_show
                    print(f"Uploading background art for {poster['title']} in {tv_show.librarySectionTitle} library.")
                elif poster["season"] >= 1:
                    if poster["episode"] == "Cover":
                        upload_target = tv_show.season(poster["season"])
                        print(f"Uploading art for {poster['title']} - Season {poster['season']} in {tv_show.librarySectionTitle} library.")
                    elif poster["episode"] is None:
                        upload_target = tv_show.season(poster["season"])
                        print(f"Uploading art for {poster['title']} - Season {poster['season']} in {tv_show.librarySectionTitle} library.")
                    elif poster["episode"] is not None:
                        try:
                            upload_target = tv_show.season(poster["season"]).episode(poster["episode"])
                            print(f"Uploading art for {poster['title']} - Season {poster['season']} Episode {poster['episode']} in {tv_show.librarySectionTitle} library.")
                        except:
                            print(f"{poster['title']} - {poster['season']} Episode {poster['episode']} not found in {tv_show.librarySectionTitle} library, skipping.")
                if poster["season"] == "Backdrop":
                    try:
                        upload_target.uploadArt(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path))
                    except:
                        print("Unable to upload last poster.")
                else:
                    try:
                        upload_target.uploadArt(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path))
                    except:
                        print("Unable to upload last poster.")
                    time.sleep(6)  # too many requests prevention
            except:
                print(f"{poster['title']} - Season {poster['season']} not found in {tv_show.librarySectionTitle} library, skipping.")
        else:
            print(f"Failed to load path for {poster['title']}.")
    else:
        print(f"{poster['title']} not found in any library.")


def upload_movie_poster(poster, movies):
    movie, show_path = find_in_library(movies, poster)
    if movie is not None:
        if show_path is not None:
            # Check if label is present and overwrite is not allowed
            label_exists = check_label_for_item(movie.ratingKey)
            if label_exists and not overwrite_labelled_shows:
                print(f"Skipping upload for {poster['title']} in {movie_item.librarySectionTitle} library as it already has the label '{append_label}'.")
                return
            
            # Define the file name
            # Check if the file already exists in the assets directory
            if asset_folders:
                file_name = f"poster.jpg"  # Adjust the naming as needed
                file_path = get_asset_file_path(assets_directory, f"movies/{show_path}", file_name)
            else:
                file_name = f"{show_path}.jpg"  # Adjust the naming as needed
                file_path = get_asset_file_path(assets_directory, f"movies", file_name)
            if os.path.exists(file_path) and not overwrite_assets:
                if only_process_new_assets:
                    print(f"Skipping upload for {poster['title']} as it already exists in {movie.librarySectionTitle} library.")
                    return
                else:
                    print(f"Using existing file for upload to {poster['title']} in {movie.librarySectionTitle} library.")
            else:
                # Save the file to the assets directory
                if asset_folders:
                    file_path = save_to_assets_directory(assets_directory, f"movies/{show_path}", file_name, poster['url'])
                else:
                    file_path = save_to_assets_directory(assets_directory, f"movies", file_name, poster['url'])
                if file_path is None:
                    print(f"Skipping upload for {show_path} {poster['title']} in {movie.librarySectionTitle} library due to download error.")
                    return

            # Upload the poster using the file path
            try:
                movie.uploadPoster(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path))
                print(f'Uploaded art for {poster["title"]}.')
                time.sleep(6)  # too many requests prevention
            except:
                print(f'Unable to upload art for {poster["title"]} in {movie.librarySectionTitle} library.')
        else:
            print(f"Failed to load path for {poster['title']}.")
    else:
        print(f"{poster['title']} not found in any library.")


def upload_collection_poster(poster, movies):
    collection_items = find_collection(movies, poster)
    if collection_items:
        for collection in collection_items:
            if collection is not None:
                if show_path is not None:
                    # Check if label is present and overwrite is not allowed
                    label_exists = check_label_for_item(collection.ratingKey)
                    if label_exists and not overwrite_labelled_shows:
                        print(f"Skipping upload for {poster['title']} in {collection.librarySectionTitle} library as it already has the label '{append_label}'.")
                        return
                    
                    # Define the file name
                    # Check if the file already exists in the assets directory
                    if asset_folders:
                        file_name = f"poster.jpg"  # Adjust the naming as needed
                        file_path = get_asset_file_path(assets_directory, f"collections/{show_path}", file_name)
                    else:
                        file_name = f"{poster['title']}_poster.jpg"  # Adjust the naming as needed
                        file_path = get_asset_file_path(assets_directory, f"collections", file_name)
                    if os.path.exists(file_path) and not overwrite_assets:
                        if only_process_new_assets:
                            print(f"Skipping upload for {poster['title']} as it already exists in {collection.librarySectionTitle} library.")
                            return
                        else:
                            print(f"Using existing file for upload to {poster['title']} in {collection.librarySectionTitle} library.")
                    else:
                        # Save the file to the assets directory
                        if asset_folders:
                            file_path = save_to_assets_directory(assets_directory, f"collections/{show_path}", file_name, poster['url'])
                        else:
                            file_path = save_to_assets_directory(assets_directory, f"collections", file_name, poster['url'])
                        if file_path is None:
                            print(f"Skipping upload for {show_path} {poster['title']} in {collection.librarySectionTitle} library due to download error.")
                            return

                    # Upload the poster using the file path
                    try:
                        collection.uploadPoster(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path))
                        print(f'Uploaded art for {poster["title"]}.')
                        time.sleep(6)  # too many requests prevention
                    except:
                        print(f'Unable to upload art for {poster["title"]} in {collection.librarySectionTitle} library.')
                else:
                    print(f"Failed to load path for {poster['title']}.")
            else:
                print(f"Failed to process {poster['title']}.")
        else:
            print(f"{poster['title']} not found in any library.")



def set_posters(url):
    print(f"Setting posters for URL: {url}")
    try:
        # Unpack the returned values safely
        result = scrape(url)
        if result is None or len(result) != 3:
            #print("Scrape function did not return the expected 3 values.")
            return
        
        movieposters, showposters, collectionposters = result
        
        if not (movieposters or showposters or collectionposters):
            print("No posters found.")
            return
        
        for poster in collectionposters:
            upload_collection_poster(poster, collections)

        for poster in movieposters:
            upload_movie_poster(poster, movies)

        for poster in showposters:
            upload_tv_poster(poster, tv)

        update_plex_labels()
    
    except Exception as e:
        print(f"Error in set_posters: {e}")


def scrape_posterdb_set_link(soup):
    try:
        view_all_div = soup.find('a', class_='rounded view_all')['href']
    except:
        return None
    return view_all_div


def scrape_posterd_user_info(soup):
    try:
        span_tag = soup.find('span', class_='numCount')
        number_str = span_tag['data-count']
        
        upload_count = int(number_str)
        pages = math.ceil(upload_count/24)
        return pages
    except:
        return None
        
def scrape_mediux_user_info(base_url):
    current_page = 1
    total_pages = 1

    while True:
        page_url = f"{base_url}?page={current_page}"
        print(f"Processing page: {current_page}")  # Print the current page number
        soup = cook_soup(page_url)

        # Find all page number links on the current page
        page_links = soup.select('a[href*="page="]')
        page_numbers = [
            int(re.search(r'page=(\d+)', a.get('href')).group(1))
            for a in page_links if re.search(r'page=(\d+)', a.get('href'))
        ]

        if page_numbers:
            total_pages = max(page_numbers)

        # Find the link to the next page
        next_page_link = soup.select_one('a[aria-label="Go to next page"]')
        if next_page_link and next_page_link.get('href'):
            match = re.search(r'page=(\d+)', next_page_link.get('href'))
            if match:
                current_page = int(match.group(1))
            else:
                break
        else:
            break

    return total_pages

def scrape_posterdb(soup):
    movieposters = []
    showposters = []
    collectionposters = []
    
    # find the poster grid
    poster_div = soup.find('div', class_='row d-flex flex-wrap m-0 w-100 mx-n1 mt-n1')

    # find all poster divs
    posters = poster_div.find_all('div', class_='col-6 col-lg-2 p-1')

    # loop through the poster divs
    for poster in posters:
        # get if poster is for a show or movie
        media_type = poster.find('a', class_="text-white", attrs={'data-toggle': 'tooltip', 'data-placement': 'top'})['title']
        # get high resolution poster image
        overlay_div = poster.find('div', class_='overlay')
        poster_id = overlay_div.get('data-poster-id')
        poster_url = "https://theposterdb.com/api/assets/" + poster_id
        # get metadata
        title_p = poster.find('p', class_='p-0 mb-1 text-break').string

        if media_type == "Show":
            title = title_p.split(" (")[0]
            try:
                year = int(title_p.split(" (")[1].split(")")[0])
            except:
                year = None
                
            if " - " in title_p:
                split_season = title_p.split(" - ")[-1]
                if split_season == "Specials":
                    season = 0
                elif "Season" in split_season:
                    season = int(split_season.split(" ")[1])
            else:
                season = "Cover"
            
            showposter = {}
            showposter["title"] = title
            showposter["url"] = poster_url
            showposter["season"] = season
            showposter["episode"] = None
            showposter["year"] = year
            showposter["source"] = "posterdb"
            showposters.append(showposter)

        elif media_type == "Movie":
            title_split = title_p.split(" (")
            if len(title_split[1]) != 5:
                title = title_split[0] + " (" + title_split[1]
            else:
                title = title_split[0]
            year = title_split[-1].split(")")[0]
                
            movieposter = {}
            movieposter["title"] = title
            movieposter["url"] = poster_url
            movieposter["year"] = int(year)
            movieposter["source"] = "posterdb"
            movieposters.append(movieposter)
        
        elif media_type == "Collection":
            collectionposter = {}
            collectionposter["title"] = title_p
            collectionposter["url"] = poster_url
            collectionposter["source"] = "posterdb"
            collectionposters.append(collectionposter)
    
    return movieposters, showposters, collectionposters


def get_mediux_filters():
    config = json.load(open("config.json"))
    return config.get("mediux_filters", None)


def check_mediux_filter(mediux_filters, filter):
    return filter in mediux_filters if mediux_filters else True


def scrape_mediux(soup):
    base_url = "https://mediux.pro/_next/image?url=https%3A%2F%2Fapi.mediux.pro%2Fassets%2F"
    quality_suffix = "&w=3840&q=80"
    
    scripts = soup.find_all('script')

    media_type = None
    showposters = []
    movieposters = []
    collectionposters = []
    mediux_filters = get_mediux_filters()
    title = None
        
    for script in scripts:
        if 'files' in script.text:
            if 'set' in script.text:
                if 'Set Link\\' not in script.text:
                    data_dict = parse_string_to_dict(script.text)
                    poster_data = data_dict["set"]["files"]

    for data in poster_data:
        if data["show_id"] is not None or data["show_id_backdrop"] is not None or data["episode_id"] is not None or data["season_id"] is not None or data["show_id"] is not None:
            media_type = "Show"
        else:
            media_type = "Movie"
                    
    for data in poster_data:        
        if media_type == "Show":
            episodes = data_dict["set"]["show"]["seasons"]
            show_name = data_dict["set"]["show"]["name"]
            try:
                year = int(data_dict["set"]["show"]["first_air_date"][:4])
            except:
                year = None

            if data["fileType"] == "title_card":
                episode_id = data["episode_id"]["id"]
                season = data["episode_id"]["season_id"]["season_number"]
                season_data = [episode for episode in episodes if episode["season_number"] == season][0]
                episode_data = [episode for episode in season_data["episodes"] if episode["id"] == episode_id][0]
                episode = episode_data["episode_number"]
                file_type = "title_card"
            elif data["fileType"] == "backdrop":
                season = "Backdrop"
                episode = None
                file_type = "background"
            elif data["season_id"] is not None:
                season_id = data["season_id"]["id"]
                season_data = [episode for episode in episodes if episode["id"] == season_id][0]
                episode = "Cover"
                season = season_data["season_number"]
                file_type = "season_cover"
            elif data["show_id"] is not None:
                season = "Cover"
                episode = None
                file_type = "show_cover"

        elif media_type == "Movie":
            if data["movie_id"]:
                if data_dict["set"]["movie"]:
                    title = data_dict["set"]["movie"]["title"]
                    year = int(data_dict["set"]["movie"]["release_date"][:4])
                elif data_dict["set"]["collection"]:
                    movie_id = data["movie_id"]["id"]
                    movies = data_dict["set"]["collection"]["movies"]
                    movie_data = [movie for movie in movies if movie["id"] == movie_id][0]
                    title = movie_data["title"]
                    year = int(movie_data["release_date"][:4])
            elif data["collection_id"]:
                title = data_dict["set"]["collection"]["collection_name"]
            
        image_stub = data["id"]
        poster_url = f"{base_url}{image_stub}{quality_suffix}"
        
        if media_type == "Show":
            showposter = {}
            showposter["title"] = show_name
            showposter["season"] = season
            showposter["episode"] = episode
            showposter["url"] = poster_url
            showposter["source"] = "mediux"
            showposter["year"] = year

            if check_mediux_filter(mediux_filters=mediux_filters, filter=file_type):
                showposters.append(showposter)
            else:
                print(f"{show_name} - skipping. '{file_type}' is not in 'mediux_filters'")
        
        elif media_type == "Movie":
            if title:
                if "Collection" in title:
                    collectionposter = {}
                    collectionposter["title"] = title
                    collectionposter["url"] = poster_url
                    collectionposter["source"] = "mediux"
                    collectionposters.append(collectionposter)
                
                else:
                    movieposter = {}
                    movieposter["title"] = title
                    movieposter["year"] = int(year)
                    movieposter["url"] = poster_url
                    movieposter["source"] = "mediux"
                    movieposters.append(movieposter)
            
    return movieposters, showposters, collectionposters

def process_boxset_url(boxset_id, soup2):
    boxset_url = f"https://mediux.pro/boxsets/{boxset_id}"
    print(f"Fetching boxset data from: {boxset_url}")
    
    scripts = soup2.find_all('script')
    data_dict = {}

    for script in scripts:
        if 'files' in script.text:
            if 'set' in script.text:
                if 'Set Link\\' not in script.text:
                    data_dict = parse_string_to_dict(script.text)
                    break  # Stop searching after finding the relevant script

    if not data_dict:
        print("No relevant script data found.")
        return []

    if 'boxset' not in data_dict or 'sets' not in data_dict['boxset']:
        print("Invalid data structure.")
        return []

    set_ids = [set_item['id'] for set_item in data_dict['boxset']['sets']]
    print(f"Extracted set IDs: {set_ids}")

    results = []
    for set_id in set_ids:
        try:
            set_results = set_posters(f"https://mediux.pro/sets/{set_id}")
            if set_results:  # Check if set_results is not None
                results.extend(set_results)  # Collect results from each set
        except Exception as e:
            print(f"Error processing set {set_id}: {e}")

    return results

def scrape(url):
    print(f"Processing URL: {url}")
    if "theposterdb.com" in url:
        print("Detected theposterdb.com URL.")
        if "/set/" in url:
            soup = cook_soup(url)
            result = scrape_posterdb(soup)
            #print(f"scrape_posterdb result: {result}")
            return result
        elif "/user/" in url:
            soup = cook_soup(url)
            result = scrape_entire_user(soup)
            #print(f"scrape_entire_user result: {result}")
            return result
        elif "/poster/" in url:
            soup = cook_soup(url)
            set_url = scrape_posterdb_set_link(soup)
            if set_url is not None:
                set_soup = cook_soup(set_url)
                result = scrape_posterdb(soup)
                #print(f"scrape_posterdb result from set URL: {result}")
                return result
            else:
                sys.exit("Poster set not found. Check the link you are inputting.")
        else:
            sys.exit("Invalid ThePosterDB URL. Check the link you are inputting.")
    elif "mediux.pro" in url:
        if "/boxsets/" in url:
            print("Detected Mediux Boxset URL.")
            boxset_id = url.split('/')[-1]
            soup2 = cook_soup(url)
            return process_boxset_url(boxset_id, soup2)
        elif "/user/" in url:
            soup = cook_soup(url)
            result = scrape_mediux_user(soup)
            #print(f"scrape_mediux_user: {result}")
            return result
        elif "/sets/" in url:
            print("Detected Mediux Set URL.")
            soup = cook_soup(url)
            result = scrape_mediux(soup)
            #print(f"scrape_mediux result: {result}")
            return result
        else:
            sys.exit("Invalid Mediux URL. Check the link you are inputting.")
    
    elif ".html" in url:
        print("Detected local HTML file.")
        with open(url, 'r', encoding='utf-8') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        result = scrape_posterdb(soup)
        #print(f"html result from local file: {result}")
        return result
    
    else:
        sys.exit("Poster set not found. Check the link you are inputting.")

# Checks if url does not start with "//", "#", or is blank
def is_not_comment(url):
    regex = r"^(?!\/\/|#|^$)"
    pattern = re.compile(regex)
    return True if re.match(pattern, url) else False

  
def parse_urls(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            urls = file.readlines()
        for url in urls:
            url = url.strip()
            if is_not_comment(url):
                if "/user/" in url.lower():
                    if "theposterdb.com" in url.lower():
                        scrape_entire_user(url)
                    elif "mediux.pro" in url.lower():
                        scrape_mediux_user(url)
                else:  
                    set_posters(url)
    except FileNotFoundError:
        print("File not found. Please enter a valid file path.")
    
def scrape_entire_user(url):
    soup = cook_soup(url)
    pages = scrape_posterd_user_info(soup)
    
    if "?" in url:
        cleaned_url = url.split("?")[0]
        url = cleaned_url
        
    for page in range(pages):
        print(f"Scraping page {page+1}.")
        page_url = f"{url}?section=uploads&page={page+1}"
        set_posters(page_url)
        
def scrape_mediux_user(url):
    print(f"Attempting to scrape '{url}' ...please be patient.")
    pages = scrape_mediux_user_info(url)
    print(f"Found {pages} pages for '{url}'")
    
    if pages is None:
        print("Error retrieving page count.")
        return
    
    if "?" in url:
        cleaned_url = url.split("?")[0]
    else:
        cleaned_url = url
        
    all_set_ids = []
    all_boxset_ids = []

    for page in range(1, pages + 1):
        print(f"Scraping page {page}.")
        page_url = f"{cleaned_url}?page={page}"
        page_soup = cook_soup(page_url)
        
        # Extract IDs from the script
        set_ids, boxset_ids = extract_ids_from_script(page_soup)
        # Print the lists before returning
        all_set_ids.extend(set_ids)
        all_boxset_ids.extend(boxset_ids)
    
    # Remove duplicates and process IDs
    unique_set_ids = list(set(all_set_ids))
    unique_boxset_ids = list(set(all_boxset_ids))
    # Print the lists before returning
    print("Processing Sets:", list(unique_set_ids))
    print("Processing Box Sets:", list(unique_boxset_ids))
    process_ids(unique_set_ids, unique_boxset_ids)

def extract_ids_from_script(soup):
    """Extract set and boxset IDs from script tags."""
    scripts = soup.find_all('script')
    data_dict = {}

    for script in scripts:
        if 'files' in script.text and 'set' in script.text:
            if 'Set Link\\' not in script.text:
                data_dict = parse_string_to_dict(script.text)
                break  # Stop searching after finding the relevant script

    if not data_dict:
        print("No relevant script data found.")
        return [], []

    # Debug output to check the structure of the parsed data
    #print("Parsed data dictionary:", data_dict)

    # Function to recursively find 'sets' in the nested structure
    def find_sets(data):
        if isinstance(data, dict):
            if 'sets' in data:
                return data['sets']
            for key, value in data.items():
                result = find_sets(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = find_sets(item)
                if result:
                    return result
        return None

    # Attempt to locate 'sets' key
    sets = find_sets(data_dict)
    
    if not sets:
        print("No 'sets' key found in the nested structure.")
        return [], []

    #print("Extracted sets:", sets)

    set_ids = set()
    boxset_ids = set()

    for item in sets:
        if 'boxset' in item and item['boxset']:
            boxset_id = item['boxset'].get('id')
            if boxset_id:
                boxset_ids.add(boxset_id)
            else:
                # Add to set_ids if boxset_id is None, Null, or not present
                if 'id' in item:
                    set_ids.add(item['id'])
        else:
            # Add to set_ids if 'boxset' is not present or is falsy
            if 'id' in item:
                set_ids.add(item['id'])

    return list(set_ids), list(boxset_ids)
    


def process_ids(set_ids, boxset_ids):
    """Create URLs and call set_posters for each ID."""
    for boxset_id in boxset_ids:
        url = f"https://mediux.pro/boxsets/{boxset_id}"
        set_posters(url)
    
    for set_id in set_ids:
        url = f"https://mediux.pro/sets/{set_id}"
        set_posters(url)
        


if __name__ == "__main__":
    # Set stdout encoding to UTF-8
    sys.stdout.reconfigure(encoding='utf-8')
    plex_setup()
    
    # arguments were provided
    if len(sys.argv) > 1:
        command = sys.argv[1]
        # bulk command was used
        if command.lower() == 'bulk':
            if len(sys.argv) > 2:
                file_path = sys.argv[2]
                parse_urls(file_path)
            else:
                print("Please provide the path to the .txt file.")
        # a single url was provided
        elif "/user/" in command.lower():
            if "theposterdb.com" in command.lower():
                scrape_entire_user(command)
            elif "mediux.pro" in command.lower():
                scrape_mediux_user(command)
        else:
            set_posters(command)
            
    # user input
    else:
        while True:
            user_input = input("Enter a ThePosterDB set (or user) or a MediUX set url: ")
            
            if user_input.lower() == 'stop':
                print("Stopping...")
                break
            elif user_input.lower() == "bulk":
                file_path = input("Enter the path to the .txt file: ")
                try:
                    with open(file_path, "r") as file:
                        urls = file.readlines()
                    for url in urls:
                        url = url.strip()
                        set_posters(url)
                except FileNotFoundError:
                    print("File not found. Please enter a valid file path.")
            elif "/user/" in user_input.lower():
                if "theposterdb.com" in user_input.lower():
                    scrape_entire_user(user_input)
                elif "mediux.pro" in user_input.lower():
                    scrape_mediux_user(user_input)
            else:
                set_posters(user_input)