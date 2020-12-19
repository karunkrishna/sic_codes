import pandas as pd
import requests
import re

pd.set_option('display.width', 1000, 'display.max_columns', 1000)

re_article_node = re.compile(r'<article.*?>(.*?)<\/article')
re_title_href = re.compile(r'href=\"(?P<href>.*?)\".*?title=\"(?P<title>.*?)\">')

def request_data(url):
    resp = requests.get(url)
    resp = str(resp.content)
    resp = resp.replace('\n', '')

    data = re_article_node.search(resp).group(0)
    data = re_title_href.findall(data)
    data = pd.DataFrame(data, columns=['href', 'title'])
    data = data[~data.href.str.lower().str.contains(('search'))]
    return data


divisions = request_data('https://www.osha.gov/data/sic-manual')

tree_structure = []
division = None
for r in divisions.itertuples():

    category = {}
    if 'division' in r.href.lower():
        division = r.title

    elif 'group' in r.href.lower():
        category['division'] = division
        category['group'] = r.title
        category['href'] = 'https://www.osha.gov' + r.href
        tree_structure.append(category)

industry_group = pd.DataFrame(tree_structure)

tree_structure = []
for g in industry_group.itertuples():
    group = request_data(g.href)
    group['division'] = g.division
    group['industry_group'] = g.group
    group.rename(columns={'title': 'industry'}, inplace=True)
    tree_structure.append(group[['division', 'industry_group', 'industry']])

export = pd.concat(tree_structure, sort=False)

export.columns = [f'{x}_name' for x in export.columns]
export['division'] = export.division_name.str.extract('\s(.*?):')
export['industry_group'] = export.industry_group_name.str.extract('\s(\d+):')
export['sic_code'] = export.industry_name.str.extract('(\d+)')
export.industry_name = export.industry_name.str.replace('(\d+)', '').str.strip()

export[['division_name', 'industry_group_name']] = export[['division_name', 'industry_group_name']].applymap(
    lambda x: x.split(':')[1:][0].strip())
export = export.reset_index().drop('index', axis=1)
export = export[['division', 'division_name', 'industry_group', 'industry_group_name', 'sic_code', 'industry_name']]

export.to_csv('sic_codes.csv', index=False)
print(export)

