import httpx
from selectolax.parser import HTMLParser
import time
import requests
import json
from dataclasses import dataclass, asdict, fields
import csv

@dataclass
class Tech:
    entity_id: str
    company_name: str
    tech_name: str
    tech_category: str

# This scrapes companies and their id's on the company search page
# request.py will scrape techs from the api request using company ids
def get_html(url, page):
    headers = {
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    res = httpx.get(url + str(page), headers=headers, follow_redirects=True)

    time.sleep(1)
    print(f'Status code: {res.status_code}') # Console annotation
    try:
        res.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        return False
    html = HTMLParser(res.text)
    return html

# Some company elements on page are emtpy so this function checks if there is an id associated with the company element
def id_exists(company):
    try:
        return company.css_first('my-item').attributes.get('entity-id')
    except AttributeError:
        return False
    
def parse_search_page(html):
    companies = html.css('div.company-unbounded-responsive')

    for company in companies:
        if id_exists(company):
            data = {
                'id' : int(company.css_first('my-item').attributes.get('entity-id')),
                'name' : company.css_first('h2.company-title-clamp').text()
            }
            yield data

def get_comapany_techs(entity_id, company_name):
    try:
        url = "https://api.builtin.com/graphql"

        payload = json.dumps({
            "operationName": "GetCompanyTechnologies",
            "query": "query GetCompanyTechnologies($id: Int!) {\n companyByID(id: $id) {\n technologies {\n name\n urlName\n categoryName\n }\n extraTechnologies {\n name\n categoryName\n }\n }\n}\n",
            "variables": {
            "id": entity_id
            }
        })
        headers = {
            'Content-Type': 'application/json',
            'Cookie': '__cf_bm=ZeNfR0EkBcvQlfEIOy1RSpX2Qn62TDVjeo56SI7G_WY-1712182970-1.0.1.1-03XZzLV25fTbcZhcoV.tAX3VeSiWsYYDPL3WjxLqDzJrMh6VdjAe7cwOjVXZE5ZDLmxODnP4c8_BBbD74YTT6A'
        }

        res = requests.request("POST", url, headers=headers, data=payload)

        data = res.json()
        techs = data['data']['companyByID']['technologies']

        for tech in techs:
            if 'engineering' in tech['categoryName']:
                new_tech = Tech(
                    entity_id = str(entity_id),
                    company_name = company_name,
                    tech_name = tech['name'],
                    tech_category= tech['categoryName']
                )
                append_to_csv(asdict(new_tech))

    except Exception as e:
        print(f"An error occurred while processing {company_name}: {str(e)}")

# This function creates/appends data to csv a new append.csv file
def append_to_csv(tech):
    field_names = [field.name for field in fields(Tech)]
    with open('append.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, field_names)
        writer.writerow(tech)

def main():
    url = 'https://builtin.com/companies?page='
    for page in range(1610, 2900):
        time.sleep(0.5)
        print(f"Scraping page: {page}") # Console Annotation
        html = get_html(url, page)
        if not html:
            break
        companies = parse_search_page(html)

        for company in companies:
            # time.sleep(0.1)
            print(f"Retreiving {company['name']}'s tech..") # Console annotation
            get_comapany_techs(company['id'], company['name'])

        print('Scraping Finished.') # Console Annotation


if __name__ == '__main__':
    main()