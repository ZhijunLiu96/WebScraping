# Project Descriptions

Goal: Use selenium to download pdf files from web database

# Steps


### Use Selenium to Scrape all meta data, and the web page urls that include the pdf download links

1. Firstly, import all packages that required

```python
from pyquery import PyQuery as pq
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from time import sleep
```

2. Make sure you have downloaded Chromedriver

```python
browser = webdriver.Chrome()
browser.get('url')
```

3. Since only a subset is required, we need to add some filter. Locate all buttons needed and click them.

<img src='figure/1.png'>

```python
# click region
button1 = browser.find_element_by_css_selector('body > div > section > div:nth-child(3) > div > div:nth-child(4) > div > div > button')
button1.click()
# click africa
button2 = browser.find_element_by_css_selector('body > div > section > div:nth-child(3) > div > div:nth-child(4) > div > div > div > ul > li:nth-child(1) > a')
button2.click()
# click search
button3 = browser.find_element_by_css_selector('#home-search-text')
button3.click()
WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "total-time")))
```

4. Use PyQuery to parse the page_source, and simulate clicking the 'next page' button

<img src='figure/2.png'>

```python
org, orglink, sz, sec, cty, reg, repo = [], [], [], [], [], [], []

for i in range(72): # 71
    sleep(0.5)
    doc = pq(browser.page_source)
    items = doc('tbody tr').items()
    for item in items:
        name = str(item('tr td h4 a').text())
        name_url = 'https://database.globalreporting.org' + item('tr td h4 a').attr('href')
        size = item('tr > td:nth-child(2)').text()
        sector = item('tr > td:nth-child(3)').text()
        country = item('tr > td:nth-child(4) > img').attr('src')[-6:-4]
        region = item('tr> td:nth-child(5)').text()
        report = []
        reports = item('tr > td:nth-child(6) a').items()
        for r in reports:
            year = r('a span:nth-child(1)').text()
            # label = r('a span:nth-child(2)').text()
            url = '///////' + r('a').attr('href')
            report.append(year+': '+url)
        org.append(name)
        orglink.append(name_url)
        sz.append(size)
        sec.append(sector)
        cty.append(country)
        reg.append(region)
        repo.append(report)
    sleep(0.5)
    # don't click last page
    if i == 71:
        break
    WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="results-datatable_next"]/a'))).click()
    sleep(0.5)

df = pd.DataFrame({'ORG Name': org, 'ORG Link': orglink, 'Size':sz, 'Sector': sec, 'Country': cty, 'Region': reg, 'Report':repo})
```

For each record appeared, there might be multiple reports. Append all reports' urls in a list.

```python
for r in reports:
	year = r('a span:nth-child(1)').text()
    # label = r('a span:nth-child(2)').text()
    url = '///////' + r('a').attr('href')
    report.append(year+': '+url)
```

4. Save the dataframe to "download.csv"


### Make the urls that could directly access pdf files

If we go to the download page and click the download button, we need to pass the Captcha, which is a challenge for web crawlers. But in this case, I found a way to avoid this problem.

<img src='figure/3.png'>

If we open the pdf file, the download link is as follow:
```
https://sdd-pdf.s3.amazonaws.com/report-pdfs/2014/name.pdf?AWSAccessKeyId=key&Expires=1598662304&Signature=L1Vc5az2kDV%2BfjstZEtCVXzZy3w%3D
```
Let's try to search for the AWSAccessKey on the web script. It is so amazing, each the picture of pdf cover share the similiar key with the file.

<img src='figure/4.png'>

Just make a little bit modification!

<img src='figure/5.png'>

1. A function to adapt the cover url to the corresponding pdf url.
```python
def generate_download_url(url):
    url = re.sub('report-covers','report-pdfs',url)
    url = re.sub('/profile.jpg','.pdf',url)
    result = re.search('(.*?AWSAccessKeyId.*?AKIAJZQ4KYD2D35QKCDA).*?',url,re.S)
    return result.group(1)
```

2. Use selenium to get the cover url, the function returns two things, a list of file names, and a list of file urls.

```python
def get_token(urls):
    names, links = [], []
    for url in urls:
        try:
            result = re.search('(\d.*?)\:\s(http.*?$)', url, re.S)
            name = result.group(1)
            link = result.group(2)
            browser = webdriver.Chrome()
            browser.set_window_size(50, 100)
            browser.get(link)
            doc = pq(browser.page_source)
            browser.close()
            # get the token
            text = doc('body > div > div > div.col-md-4 > img').attr('src')
            link = generate_download_url(text)
            file_name = re.search('.*?report-pdfs(.*?pdf.*?)AWSAccessKeyId.*?', link, re.S)
            file_name = file_name.group(1)
            file_name = file_name[6:-1]
            names.append(name + '' + file_name)
            links.append(link)
        except: pass
    return names, links
```


### Finally, download all files to local or Google drive

If you want to download to google Drive, use Colab and connect to your drive.

```python
from google.colab import drive
drive.mount('/content/drive/')
```

Import all packages required.

```python
import ast
import requests
import pandas as pd
```

Function to download with default name:

```python
def download(url):
    r = requests.get(url, stream=True)
    name = url[50:-36]
    path = 'data/'+name
    with open(path, 'wb') as f:
        f.write(r.content)
```

Loop our urls in the csv, and track the progress

```python
data = pd.read_csv('download.csv')
urls_all = list(data['download'])
for i in range(len(urls_all)):
    urls = ast.literal_eval(urls_all[i])
    for url in urls:
        try:
            download(url)
        except: print('error')
    print(i+1)
```

