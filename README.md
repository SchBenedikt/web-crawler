# web-crawler

A simple web crawler using Python that stores the metadata of each web page in a database.

## Purpose and Functionality

The web crawler is designed to crawl web pages starting from a base URL, extract metadata such as title, description, image, locale, and type, and store this information in a MongoDB database. The crawler can handle multiple levels of depth and respects the `robots.txt` rules of the websites it visits.

## Dependencies

The project requires the following dependencies:

- `requests`
- `beautifulsoup4`
- `pymongo`

You can install the dependencies using the following command:

```bash
pip install -r requirements.txt
```

## Setting Up and Running the Web Crawler

1. Clone the repository:

```bash
git clone https://github.com/schBenedikt/web-crawler.git
cd web-crawler
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure that MongoDB is running on your local machine. The web crawler connects to MongoDB at `localhost:27017` and uses a database named `search_engine`.

4. Run the web crawler:

```bash
python crawler.py
```

## Example Usage

The web crawler starts from the base URL `https://github.com/schBenedikt` and extracts metadata from each page it visits. The metadata is then stored in the `meta_data` collection of the `search_engine` database in MongoDB.

Here is an example of how the metadata is stored in the database:

```json
{
  "url": "https://github.com/schBenedikt",
  "title": "schBenedikt - GitHub",
  "description": "GitHub profile of schBenedikt",
  "image": "https://avatars.githubusercontent.com/u/12345678?v=4",
  "locale": "en_US",
  "type": "profile"
}
```

The web crawler will print the metadata of each page it visits to the console and save it to the database. If a page is not reachable, the corresponding entry will be deleted from the database.

## Notes

- The web crawler respects the `robots.txt` rules of the websites it visits.
- The web crawler can handle multiple levels of depth, which can be configured in the `get_meta_data_from_url` function.
