# Plex Poster Set Helper

### With Kometa-style assets & MediUX boxset/user compatibility

**Plex Poster Set Helper** is a tool designed to streamline the process of uploading poster sets from [**ThePosterDB**](https://theposterdb.com) or [**MediUX**](https://mediux.pro/) to your Plex server in seconds!  

This fork includes additional features and improvements to enhance functionality. Future updates or bug fixes may or may not be added.

## Installation

1. [Install Python](https://www.python.org/downloads/) (if not installed already)

2. Extract all files into a folder

3. Open a terminal in the folder

4. Install the required dependencies using:

```bash
pip install -r requirements.txt
```

5. Rename `example_config.json` to `config.json`, and populate it with the proper information
    - "base_url"
        - the IP and port of your Plex server. e.g. "http://12.345.67.890:32400/"
    - "token"
        - your Plex token
        - **NOTE: this can be found [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)**
    - "tv_library"
        - the name of your TV Shows library (e.g. "TV Shows")
        - multiple libraries are also supported, check the `Multiple Libraries` section of the README
    - "movie_library"
        - the name of your Movies library (e.g. "Movies")
        - multiple libraries are also supported, check the `Multiple Libraries` section of the README
    - "plex_collections"
        - the name of your libraries with collections (e.g. "Movies, TV Shows")
    - "mediux_filters"
        - including any of these flags will have the script *upload* those media types to Plex.
            - `show_cover`
            - `background`
            - `season_cover`
            - `title_card`
    - "append_label"
        - This label is applied in Plex to all items with assets applied through the script.
    - "assets_directory"
        - Asset folder name, located in the same folder as the script.
    - "asset_folders": true
        - Enable the use of Kometa-style asset folders.
    - "overwrite_existing_assets"
        - Enable overwriting of saved assets with new ones from scraped sources. (Can be passed via command line using `-OE`)
    - "overwrite_labelled_shows"
        - Enable the overwriting of library items with the label set in "append_label". (Can be passed via command line using `-OL`)
    - "only_process_new_assets"
        - When combined with *overwrite_labelled_shows (true)*, only update posters for items in labeled shows that do not already have assets saved. (Can be passed via command line using `-ON`)

## Simple Usage

- Run `plex_poster_set_helper.py`

## Supported Features

### Multiple Libraries

To utilize multiple libraries, update the `config.json` as follows:

```bash
"tv_library": ["TV Shows", "Kids TV Shows"],
"movie_library": ["Movies", "Kids Movies"]
```

To clarify, use the names of your libraries, those are just placeholders. If the media is in both libraries, the posters will be replaced in both libraries.

### Bulk Import

1. Enter `bulk` in the first input prompt
2. Enter the path to a .txt file (eg. `example_bulk_import.txt`)

### Command line argument variables
Command line arguments are supported.

- Passing a single link e.g.`plex_poster_set_helper.py https://mediux.pro/sets/9242` or `plex_poster_set_helper.py https://mediux.pro/user/XXYYZZ/sets`

- Passing a bulk import file e.g. `plex_poster_set_helper.py bulk example_bulk_import.txt`

- Passing variables e.g. `plex_poster_set_helper.py bulk new.txt -OE true --OL true --NA false`

### Kometa-Style Asset Creation
By default, the script creates assets that follow the standard Kometa (Plex-Meta-Manager) format. Configuration options are listed under `Installation`

