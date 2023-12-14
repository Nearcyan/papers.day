import argparse
import shutil
import tempfile
import django
import fitz
import openai
import random
import requests
import re

from scholarly import scholarly # if this breaks, run pip install --upgrade httpx
from scholarly import ProxyGenerator
from datetime import datetime
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.conf import settings

import tarfile
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'papers.settings')
django.setup()
from backend.models import ArxivPaper, Author, Subject, PaperImage, PaperSource
print(f'Found {len(settings.INTERESTING_DOMAINS)} domains of interest')


def extract_tar_gz(file_path: str, output_dir: str) -> None:
    """
    Extract a tar.gz file to the specified output directory
    :param file_path: The path to the tar.gz file
    :param output_dir: The directory to extract the tar.gz file to
    :return: None
    """
    with tarfile.open(file_path, 'r:gz') as tar:
        tar.extractall(output_dir)


def create_image_objects(directory: str, paper) -> list:
    """
    Given a directory which contains images, this function will create PaperImage objects for each image
    :param directory: The directory containing the images
    :return: The list of PaperImage objects
    """
    image_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files if
                   f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    images = []
    for image_file in image_files:
        image_path = os.path.join(directory, image_file)
        with open(image_path, 'rb') as file:
            filename = paper.arxiv_id + '_' + os.path.basename(image_path)
            django_file = ContentFile(file.read(), name=filename)
            image = PaperImage(image=django_file, paper=paper)
            image.save()
            images.append(image)

    return images


def create_tex_files(directory: str, paper) -> list:
    """
    Given a directory which contains tex files, this function will create PaperSource objects for each tex file
    :param directory: The directory containing the tex files
    :return: The list of PaperSource objects
    """
    tex_files = [f for f in os.listdir(directory) if f.lower().endswith('.tex')]
    sources = []
    for tex_file in tex_files:
        tex_path = os.path.join(directory, tex_file)
        with open(tex_path, 'r') as f:
            tex_content = f.read()
        source = PaperSource(content=tex_content, paper=paper)
        source.save()
        sources.append(source)

    return sources


def delete_files(directory: str) -> None:
    """
    Delete all files in a directory
    :param directory: The directory to delete the files from
    :return: None
    """
    for root, dirs, files in os.walk(directory):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def get_paper_screenshot_from_pdf(pdf_path) -> str:
    """
    Get a screenshot of the first page of the pdf
    :param pdf_path: The path to the pdf
    :return: The path to the screenshot
    """
    try:
        pdf = fitz.open(pdf_path)
        page = pdf.load_page(0)
        pix = page.get_pixmap(alpha=False)
        random_int = random.randint(0, 1000000)
        temp_filename = f'temp_{random_int}.png'
        pix.save(temp_filename, "png")
        return temp_filename
    except Exception as e:
        print(f'Error occurred while getting screenshot of pdf: {pdf_path}')
        return None


def get_paper_summary_from_abstract(abstract: str) -> str:
    """
    Get a summary of the paper from the abstract
    :param abstract: The abstract of the paper
    :return: The summary of the paper
    """
    openai.api_key = settings.OPENAI_API_KEY
    prompt = f"Summarize the following AI paper abstract in two sentences:\nAbstract: {abstract}\nSummary:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.9,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
    )
    summary = response.choices[0].text
    return summary.strip()


def scrape_paper(arxiv_id, google_scholar=False):
    """
    Scrape the paper with the given arxiv_id and save it to the database
    :param arxiv_id: The arxiv_id of the paper
    :param google_scholar: True if google scholar lookups should be performed, else false
    :return: The saved ArxivPaper object
    """
    # Send a GET request to the URL and retrieve the HTML content
    url = f'https://arxiv.org/abs/{arxiv_id}'
    if ArxivPaper.objects.filter(arxiv_id=arxiv_id).exists():
        print(f'[{arxiv_id}] Paper with id {arxiv_id} already exists')
        return None
    else:
        print(f'[{arxiv_id}] Scraping paper: {url}')

    try:
        response = requests.get(url)
        html_content = response.content
    except Exception as e:
        print(f'[{arxiv_id}] Error occurred while scraping {url}')
        return None

    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Get the title
    title_tag = soup.find('h1', class_='title')
    title = title_tag.get_text(strip=True)
    title = re.sub(r'Title:', '', title)
    print(f'[{arxiv_id}] Title: {title}')

    # Get the abstract
    abstract_tag = soup.find('blockquote', class_='abstract')
    abstract = abstract_tag.get_text(strip=True)
    # remove various things
    abstract = re.sub(r'Abstract:', '', abstract)
    abstract = re.sub(r'\n', ' ', abstract)
    abstract = re.sub(r'  ', ' ', abstract)

    # Get the authors
    author_div = soup.find('div', class_='authors')
    author_tags = author_div.find_all('a')
    authors = [author.get_text(strip=True) for author in author_tags]

    # Get the primary subject
    primary_subject = soup.find('span', class_='primary-subject').get_text(strip=True)
    short_name = primary_subject.split('(')[1].replace(')', '').strip()
    full_name = primary_subject.split('(')[0].strip()
    print(f'[{arxiv_id}] Primary subject: {short_name} - {full_name}')
    prim_subject = Subject.objects.filter(short_name=short_name).first()
    if not prim_subject:
        prim_subject = Subject.objects.create(short_name=short_name, full_name=full_name)
        print(f'[{arxiv_id}] Creating subject: {short_name} - {full_name}')

    # get everything inside of 'subjects' that is not in a <span>:
    subject_div = soup.find('td', class_='subjects')
    subject_text = subject_div.get_text(strip=True)
    subject_text = re.sub(r'<span.*span>', '', subject_text)
    subject_list = subject_text.split(';')
    subject_list = [subject.strip() for subject in subject_list]
    subjects = [subject for subject in subject_list if subject]

    jref = soup.find('td', class_='tablecell jref')
    if jref:
        jref = jref.get_text(strip=True)
        jref = re.sub(r'Journal ref:', '', jref)
        jref = re.sub(r'\n', '', jref)
        jref = re.sub(r'  ', '', jref)
        print(f'[{arxiv_id}] Journal ref: {jref}')
    else:
        jref = None

    comments = soup.find('td', class_='tablecell comments')
    if comments:
        comments = comments.get_text(strip=True)
        comments = re.sub(r'Comments:', '', comments)
        comments = re.sub(r'\n', '', comments)
        comments = re.sub(r'  ', '', comments)
        print(f'[{arxiv_id}] Comments: {comments}')
    else:
        comments = None

    doi = soup.find('td', class_='tablecell arxivdoi')
    if doi:
        doi = doi.find('a')
        doi = doi.get_text(strip=True)
        doi = re.sub(r'DOI:', '', doi)
        doi = re.sub(r'\n', '', doi)
        doi = re.sub(r'  ', '', doi)
        print(f'[{arxiv_id}] DOI: {doi}')
    else:
        doi = None

    # Get the date
    date_tag = soup.find('div', class_='dateline')
    date_string = date_tag.get_text(strip=True)
    date_string = re.sub(r' \(v.*\)', '', date_string)
    date_match = re.search(r'\[Submitted on (.+)\]', date_string)
    if date_match:
        date_string = date_match.group(1)
        date = datetime.strptime(date_string, '%d %b %Y').date()
    else:
        date = None

    # Download the pdf
    pdf_url = f'https://arxiv.org/pdf/{arxiv_id}.pdf'
    try:
        pdf_response = requests.get(pdf_url)
        if pdf_response.status_code != 200:
            print(f'[{arxiv_id}] Error occurred while downloading pdf from {pdf_url}')
            return None
    except Exception as e:
        print(f'[{arxiv_id}] Error occurred while downloading pdf from {pdf_url}: {e}')
        return None
    pdf_content = pdf_response.content
    pdf_file = ContentFile(pdf_content, name=f'{arxiv_id}.pdf')

    # Download the source
    source_url = f'https://arxiv.org/e-print/{arxiv_id}'
    try:
        source_response = requests.get(source_url)
        print(f'[{arxiv_id}] Downloading source from {source_url}')
        if source_response.status_code != 200:
            print(f'[{arxiv_id}] Error occurred while downloading source from {source_url}')
            return None
    except Exception as e:
        print(f'[{arxiv_id}] Error occurred while downloading source from {source_url}: {e}')
        return None

    source_content = source_response.content
    source_tar = ContentFile(source_content, name=f'{arxiv_id}.tar.gz')

    paper = ArxivPaper.objects.create(title=title, abstract=abstract, publication_date=date, arxiv_id=arxiv_id, doi=doi,
                                        pdf=pdf_file, primary_subject=prim_subject, journal_ref=jref, comment=comments,
                                        source_tar=source_tar)

    # extract the source:
    temp_dir = tempfile.mkdtemp()
    try:
        extract_tar_gz(paper.source_tar.path, temp_dir)
        # grab all images from the source:
        images = create_image_objects(temp_dir, paper)
        for image in images:
            paper.images.add(image)
        print(f'[{arxiv_id}] Added {len(images)} images')
        sources = create_tex_files(temp_dir, paper)
        for source in sources:
            paper.sources.add(source)
        print(f'[{arxiv_id}] Added {len(sources)} sources')
    except Exception as e:
        print(f'[{arxiv_id}] Error occurred while extracting source: {e}')
        # not a fatal exception, some papers do not provide tar.gz files and the source can just be e.g. a pdf
    finally:
        delete_files(temp_dir)

    # Get a screenshot
    screenshot_path = get_paper_screenshot_from_pdf(paper.pdf.path)
    if screenshot_path:
        screenshot = ContentFile(open(screenshot_path, 'rb').read(), name=f'{arxiv_id}.png')
        paper.screenshot = screenshot
        os.remove(screenshot_path)

    # get a summary
    try:
        summary = get_paper_summary_from_abstract(paper.abstract)
        paper.summary = summary
        paper.save()
    except Exception as e:
        paper.delete()
        return None

    # get number of citations
    if google_scholar:
        try:
            search_query = scholarly.search_pubs(f'"{paper.title}"', patents=False, citations=False)
            first_paper_result = next(search_query)
            citations = first_paper_result['num_citations']
            paper.citations = citations
            paper.save()
            print(f'[{arxiv_id}] Citations: {citations}')
            if citations > 1000:
                interesting_paper = True
                print(f'[{arxiv_id}] Interesting paper: {citations} citations')
        except Exception as e:
            print(f'[{arxiv_id}] Could not find paper on Google Scholar')

    total_author_citations = 0
    for author_name in authors:
        # get author if exists:
        author = Author.objects.filter(name=author_name).first()
        if not author and google_scholar:
            search_query = scholarly.search_author(author_name)
            try:
                first_author_result = next(search_query)
                affiliation = first_author_result['affiliation']
                email_domain = first_author_result['email_domain'].replace('@', '')
                scolar_id = first_author_result['scholar_id']
                citations = first_author_result['citedby']

                for interesting_domain in settings.INTERESTING_DOMAINS:
                    if interesting_domain in email_domain:
                        interesting_paper = True
                        print(f'[{arxiv_id}] Interesting paper: {email_domain} email domain')
                        break
                author = Author.objects.create(name=author_name, affiliation=affiliation, email_domain=email_domain,
                                               scholar_id=scolar_id, citations=citations)
                print(f'[{arxiv_id}] Author created: {author} [affiliation: {affiliation}, email_domain: {email_domain}, citations: {citations}]')
            except StopIteration:
                author = Author.objects.create(name=author_name)
                print(f'[{arxiv_id}] Author created: {author}, could not find more information')
            except KeyError:
                author = Author.objects.create(name=author_name)
                print(f'[{arxiv_id}] Author created: {author}, key error')
            except Exception as e:
                author = Author.objects.create(name=author_name)
                print(f'[{arxiv_id}] [Google Scholar Lookup Failed] Author created: {author}')
        elif not author:
            author = Author.objects.create(name=author_name)
            print(f'[{arxiv_id}] Author created: {author}, no GS lookup')
        elif author.email_domain:
            email_domain = author.email_domain
            for interesting_domain in settings.INTERESTING_DOMAINS:
                if interesting_domain in email_domain:
                    interesting_paper = True
                    print(f'[{arxiv_id}] Interesting paper: {email_domain} email domain')
                    break
        total_author_citations += author.citations
        paper.authors.add(author)

    paper.total_author_citations = total_author_citations
    if total_author_citations > 100000:
        print(f'[{arxiv_id}] Interesting paper: {total_author_citations} total author citations')

    for subject_name in subjects:
        short_name = subject_name.split('(')[1].replace(')', '').strip()
        full_name = subject_name.split('(')[0].strip()
        print(f'[{arxiv_id}] Subject: {short_name} - {full_name}')
        subject = Subject.objects.filter(short_name=short_name).first()
        if not subject:
            subject = Subject.objects.create(short_name=short_name, full_name=full_name)
            print(f'[{arxiv_id}] Creating subject: {short_name} - {full_name}')
        paper.subjects.add(subject)

    paper.save()
    print(f'[{arxiv_id}] Paper saved: {paper}')
    print(f'[{arxiv_id}] [INTERESTING] Paper was interesting!: {paper}')
    return paper


def scrape_papers_from_list(section, num_papers, page, google_scholar=False):
    """
    Given a list url such as https://arxiv.org/list/cs.LG/pastweek?show=557, we get all paper IDs on the results
    page and then scrape each paper into our DB
    :param section: the section of the paper, e.g. cs.LG
    :param num_papers: the number of papers to scrape
    :param page: the page to get papers to scrape from
    :param google_scholar: whether to scrape google scholar for citations
    :return: None
    """
    # Send a GET request to the webpage
    list_url = f'https://arxiv.org/list/{section}/{page}?show={num_papers}'
    response = requests.get(list_url)

    # Create a BeautifulSoup object to parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all span tags with class "list-identifier"
    span_tags = soup.find_all('span', class_='list-identifier')

    # Extract the paper IDs from the anchor tags
    paper_ids = []
    for span_tag in span_tags:
        # Find the 'a' element within the span tag
        a_tag = span_tag.find('a')
        if a_tag and '/abs/' in a_tag['href']:
            # Extract the text from the 'a' element
            paper_id = a_tag.text.strip()
            paper_id = paper_id.replace('arXiv:', '')
            paper_ids.append(paper_id)

    # Print the extracted paper IDs
    for paper_id in paper_ids:
        print(f'Found paper ID: {paper_id}')
        scrape_paper(paper_id, google_scholar)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Process paper details')
    parser.add_argument('-n', '--num_papers', type=int, default=500, help='Number of papers to scrape')
    parser.add_argument('-s', '--section', type=str, default='cs.LG', help='Section of arxiv to scrape from')
    parser.add_argument('-p', '--page', type=str, default='pastweek', help='Page from arxiv to scrape from')
    parser.add_argument('-gs', '--google_scholar', type=bool, default=False, help='Enable/Disable google scholar lookups')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_arguments()
    if args.google_scholar:
        print(f'Using google scholar')
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)
    else:
        print(f'Not using google scholar')
    scrape_papers_from_list(args.section, args.num_papers, args.page, args.google_scholar)
