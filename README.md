# papers.day
https://papers.day/

papers.day scrapes ML+AI papers from arxiv and presents them in a simple and searchable manner with summaries and images.

This project is written in django with a small amount of vanilla javascript.

## Contributing
Contributors are actively desired!

Please check the issues tab for things to work on. 
Together we can make an amazing and free arxiv front-end!


## Installation
1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `cp .env.example .env`
5. `python manage.py migrate`

## Running
To run the web server, run:
- `python manage.py runserver`

To scrape papers, run:
- `python scrape_abs.py`

Note that an OpenAI API key is required in `.env` to summarize papers.


## Production
This repository is currently hosted on https://papers.day/

This service will continue to be ran for free for the foreseeable future.