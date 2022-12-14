import requests as rq
from bs4 import BeautifulSoup as bs
import json
import re
import pandas as pd


# Replace euro sizes for russian sizes and error correction
def replace_size(size):
    replace_dict = {'В': 'B', 'С': 'C', 'Е': 'E', 'чёрный': '', 'розовый': '',
                    'нет в наличии.': '', ' ': ''}
    for i in replace_dict:
        if i in size:
            size = size.replace(i, replace_dict[i])
    size = re.sub(r"\([^()]*\)", "", size)
    if '(' in size or ')' in size:
        size = ''
    try:
        size = str(int(size[:2]) + 6) + size[2:]
    except Exception:
        size = None
        print('Error of size')
    return size


def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15'
    }
    # Login page
    url = 'http://mewa-styl.ru/reg/auth'

    # Parameters for log in
    data = {
        'login': '',
        'pass': '',
        'send': '%D0%92%D0%BE%D0%B9%D1%82%D0%B8',
        'js-check': 'js-enabled'
    }

    s = rq.Session()
    auth = s.post(url=url, data=data, headers=headers)
    ulr_products = 'http://mewa-styl.ru/ishop/1_0'
    html = s.get(ulr_products).text
    # Get products links
    soup = bs(html, 'html.parser')
    urls = soup.find_all('a', class_='show_product')
    urls = [i.get('href') for i in urls]
    print('Total: ', len(urls))

    products = {}
    count = 0

    # Get price and sizes for products
    for i in urls:
        count += 1
        html = s.get(i).text
        soup = bs(html, 'html.parser')
        try:
            products[i] = [
                i.replace('http://mewa-styl.ru/ishop/product/', ''),
                soup.find('h1', class_='prod_title').text,
                soup.select('div.product_dop_modes_content p')[0].get_text().replace(u'\xa0', u' '),
                soup.select('div.prod_price span.price')[0].get_text(),
                soup.find('a', class_='highslide').get('href'),
                ', '.join([replace_size(i.get_text().rstrip()) for i in soup.select('span.radio_size label')])
            ]
        except Exception:
            print(i, Exception)
            products[i] = [''] * 6
        print(f'Processed: {count}/{len(urls)}')

    # Dump in json
    with open('products.json', 'w') as prods:
        json.dump(products, prods, ensure_ascii=False, indent=4)

    data = pd.read_json('products.json', orient='index')
    data.columns = ['id', 'name', 'desc', 'price', 'img', 'size']
    data = data[data['size'] != '']

    # Create xml
    with open('gabbiano.xml', 'w') as file:
        file.write(data.to_xml())
        print('XML is created')


if __name__ == '__main__':
    main()
