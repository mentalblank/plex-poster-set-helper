# Plex Poster Set Helper

### Enhanced with Kometa-Style Assets & MediUX Boxset/User Compatibility

**Plex Poster Set Helper** is a tool for automatically uploading poster sets from [**ThePosterDB**](https://theposterdb.com) and [**MediUX**](https://mediux.pro/) to your Plex server in just a few seconds.

This fork includes several enhancements and optimisations and was also heavily edited before a UI was added in the original repo. I do not need the UI as I run all commands via command line and additional scripts, so I do not intend to add it. Updates and bug fixes **might** be provided, but most likely will not.

## Features

- **Automated Poster Uploads**: Effortlessly upload sets of posters to your Plex server from **ThePosterDB** or **MediUX**.
- **Kometa-Style Assets**: Integrates polished, high-quality poster assets for a refined look.
- **MediUX Boxset/User Compatibility**: Compatible with MediUX’s boxsets and user-specific configurations for better media organisation.
- **Multiple Library Support**: Manage assets across multiple Plex libraries for both TV Shows and Movies.
- **Advanced Configuration Options**: Full flexibility with asset management and media types for upload.

## Installation

### Prerequisites

1. **Install Python** (if not already installed): [Download Python](https://www.python.org/downloads/)

2. **Clone or download the repository** to a folder of your choice.

### Steps

1. **Navigate to the folder** where you extracted or cloned the files.

2. **Open a terminal** or command prompt in that folder.

3. **Install Dependencies**: Run the following command to install the necessary libraries:

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure the Script**:
   - Rename `example_config.json` to `config.json`.
   - Open `config.json` and fill in the following details:
   
     - **base_url**: The URL and port of your Plex server (e.g., `http://12.345.67.890:32400/`).
     - **token**: Your Plex authentication token (Find it [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)).
     - **tv_library**: The name of your Plex TV Shows library (e.g., `"TV Shows"`).
     - **movie_library**: The name of your Plex Movies library (e.g., `"Movies"`).
     - **plex_collections**: Specify libraries that contain collections (e.g., `"Movies, TV Shows"`).
     - **mediux_filters**: Select the media types to upload to Plex:
       - `show_cover`
       - `background`
       - `season_cover`
       - `title_card`
     - **append_label**: Label to be applied to all items with assets added by the script.
     - **assets_directory**: Folder name where your assets are stored (relative to the script’s directory).
     - **asset_folders**: Enable Kometa-style asset folders (`true` or `false`).
     - **overwrite_existing_assets**: Set to `true` to overwrite existing assets. (Command-line flag: `-OE`).
     - **overwrite_labelled_shows**: Enable overwriting items with the specified `append_label` in your libraries. (Command-line flag: `-OL`).
     - **only_process_new_assets**: When used with `overwrite_labelled_shows`, updates only items that don’t already have assets. (Command-line flag: `-ON`).

## Usage

Once configured, run the script to upload poster sets to your Plex server. The script will retrieve and apply the appropriate assets based on the settings you've defined.

### Example Commands
- To upload a **single poster set**, pass the link directly:  
  ```bash
  plex_poster_set_helper.py https://mediux.pro/sets/9242```
- To upload **user specific sets**:
  ```bash
  plex_poster_set_helper.py https://mediux.pro/user/USERNAME/sets```
- To **bulk import** poster sets from a text file:
  ```bash
  plex_poster_set_helper.py bulk example_bulk_import_file.txt```
- To **pass variables** with specific flags:
  ```bash
  plex_poster_set_helper.py bulk new.txt -OE true --OL true --NA false```

### Command-Line Arguments

- `-OE`: Enable overwriting of existing assets with new ones.
- `-OL`: Overwrite library items marked with the `append_label`.
- `-ON`: Only process and update assets for items that do not have existing assets. 

## Multiple Library Support

You can configure the script to handle multiple libraries for both TV Shows and Movies by listing the library names separated by commas in the configuration file. Example:

```json
"tv_library": ["TV Shows", "Kids TV Shows"],
"movie_library": ["Movies", "Kids Movies"]
```
> To clarify, use the names of your libraries; those are just placeholders. If the media is in both libraries, the posters will be replaced in both libraries.
