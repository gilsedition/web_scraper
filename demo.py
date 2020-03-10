import pandas as pd
import lxml.html as lh
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import random
import urllib.request
import pdfquery
from lxml import etree
import re

# domiciles = ['Austria', 'Belgium', 'Chile','Czech Republic','Finland','France','Germany','Greece','Iceland',
#              'Ireland','Italy','Liechtenstein','Luxembourg','Netherlands','Norway','Portugal','South Africa',
#              'Spain','Sweden','Switzerland','United Kingdom']

col_order = ['Asset Manager','Fund name','URL','NAV_currency','NAV','NAV Date',
             'AUM_currency','AUM','AUM in Millions','AUM Date','History of Operations(yrs)','Domicile',
             'Performance(%,annualised-3yr)','Volatility(3yr)','Standard Deviation',
             'Concentration in investment(top 10 holdings)','Expense Ratio','Currency','ISIN','CUSIP',
             'Fund Code','SEDOL','Launch Date','Bloomberg Ticker']


language_dict = {'Austria':'Fondsvermögen (in Mio.)', 'France': '', 'Germany':'Fondsvermögen (in Mio.)',
                 'Italy': 'Patrimonio netto (in mln.)','Liechtenstein':'Fondsvermögen (in Mio.)',
                 'Luxembourg':'Total net assets (in millions)', 'Spain':'Patrimonio (en mill.)'}

language_cols = {'Austria': {'Fondsname': 'Fund name', 'Emissionswhrung': 'Currency', 
        'Fondsdomizil': 'Domicile', 'Bloomberg-Code': 'Bloomberg Ticker'},
                'France': {'Nom du fonds': 'Fund name', 'Devise au lancement': 'Currency', 
        'Domicile du fonds': 'Domicile', 'Bloomberg Code': 'Bloomberg Ticker'},
                'Germany': {'Fondsname': 'Fund name', 'Emissionswhrung': 'Currency', 
        'Fondsdomizil': 'Domicile', 'Bloomberg-Code': 'Bloomberg Ticker'},
                'Italy': {'Nome del Fondo': 'Fund name', 'Valuta di emissione': 'Currency', 
        'Domicilio del fondo': 'Domicile', 'Bloomberg Codice': 'Bloomberg Ticker'},
                'Liechtenstein': {'Fondsname': 'Fund name', 'Emissionswhrung': 'Currency', 
        'Fondsdomizil': 'Domicile', 'Bloomberg-Code': 'Bloomberg Ticker'},
                'Spain': {'Fund Name': 'Fund name', 'Fund Currency': 'Currency', 
        'Fund Domicile': 'Domicile', 'Código Bloomberg': 'Bloomberg Ticker'}}

default_cols = {'Fund Name': 'Fund name', 'Fund Currency': 'Currency', 
        'Fund Domicile': 'Domicile', 'Bloomberg code': 'Bloomberg Ticker'}

chrome_path = "D:\IBEX\Gil\chromedriver_win32\chromedriver"
chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_experimental_option('useAutomationExtension', False)
driver=webdriver.Chrome(chrome_path, options=chromeOptions)
landing_page = "https://amfunds.credit-suisse.com/global/en"
driver.get(landing_page)

domicile_dropdown = driver.find_element_by_name('seldomiciles')
domiciles = [dom.text for dom in domicile_dropdown.find_elements_by_tag_name('option')]

df_list = []

def read_links(country_name):
    data_list = []
    data = pd.read_csv('Links/{}_links.csv'.format(country_name))
    # xxxxxxxxxxxxxxx Control here to TEST xxxxxxxxxxxxxxx
    for row in data.itertuples():
        fund_data = scrape_data(row[2], country_name)
        if fund_data:
            data_list.append(fund_data)
    scraped_data = pd.DataFrame(data_list)
    scraped_data.rename(columns=language_cols.get(country_name,default_cols), inplace=True)
    print('=========={} extraction completed ========= '.format(country_name))
    try:
        scraped_data['NAV_currency'] = scraped_data['Currency']
        scraped_data['AUM_currency'] = scraped_data['Currency']
    except:
        scraped_data['NAV_currency'] = 'NA'
        scraped_data['AUM_currency'] = 'NA'
    data_cols = scraped_data.columns.tolist()
    for col in col_order:
        if col not in data_cols:
            scraped_data[col] = 'NA'
    domicile_df = scraped_data[col_order]
    df_list.append(domicile_df)
    domicile_df.to_csv('Data/{}_data.csv'.format(country_name), index=False)

def scrape_data(link, country_name):
    try:
        driver.get(link)
        content = (driver.page_source).encode('ascii', 'ignore')
        doc = lh.fromstring(content)
        labels = (doc.xpath("//span[@class='mod_two_column_labeled_content']/text()"))
        labels = [label.strip() for label in labels if label.strip()][:20]
        value_list = (doc.xpath("//div[@class='mod_two_column_labeled_content']/text()"))
        value_list = [val.strip() for val in value_list if val.strip()][:20]
        data_dict = dict(zip(labels,value_list))
        data_dict['NAV Date'] = doc.xpath("//span[@class='smallText date']/text()")[0].replace('(',"").replace(')',"").strip()
        data_dict['NAV'] = doc.xpath("//span[@class='bigText']/text()")[0]
        data_dict['URL'] = link
        data_dict['Asset Manager'] = 'Credit Suisse'

        # ------------- PDF Code --------------
        try:
            pdf_name = data_dict['ISIN']
            pdf_url = driver.find_element_by_xpath('//a[contains(text(),"Fact sheet")]').get_attribute("href")
            file_path = 'PDF/{}.pdf'.format(pdf_name)
            urllib.request.urlretrieve(pdf_url, file_path)
            pdf = pdfquery.PDFQuery(file_path)            
            pdf.load()
            search_word = language_dict.get(country_name, 'Total net assets (in mil.)')
            label = pdf.pq('LTTextLineHorizontal:contains("{}")'.format(search_word))
            left_corner = float(label.attr('x0'))
            bottom_corner = float(label.attr('y0'))
            right_corner =  float(label.attr('x1'))
            right_bottom =  float(label.attr('y1'))
            data_dict['AUM in Millions'] = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (
                right_corner, right_bottom-10, right_corner+102, right_bottom)).text()
            data_dict['AUM'] = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (
                right_corner, right_bottom-10, right_corner+102, right_bottom)).text()
            try:
                data_dict['AUM Date'] = re.search(r'\d{2}-\d{2}-\d{4}', pdf_url).group(0)
            except:
                data_dict['AUM Date'] = 'NA'

        except:
            data_dict['AUM in Millions'] = 'NA'
            data_dict['AUM'] = 'NA'
            data_dict['AUM Date'] = 'NA'
        # data_dict['AUM in Millions'] = doc.xpath("//span[@class='bigText']/text()")[1]
        # data_dict['AUM'] = doc.xpath("//span[@class='bigText']/text()")[1]
        # data_dict['AUM Date'] = doc.xpath("//span[@class='smallText date']/text()")[1].replace('(',"").replace(')',"").strip()
            print('No PDF available')
        return data_dict
        # data_list.append(data_dict)
    except:
        print(link)

for country_name in domiciles:
    if driver.current_url != landing_page:
        driver.get(landing_page)   
    select = Select(driver.find_element_by_id('seldomiciles'))
    select.select_by_visible_text(country_name)

    try:
        investor_select = Select(driver.find_element_by_id('selInvestorTypes_CH'))
        investor_select.select_by_visible_text('Qualified Investor')
    except:
        print('No Investor dropdown')

    # ============ accept button =================
    try:
        button = driver.find_element_by_class_name(u"mod_flexible_sidebar_cta_button")
        driver.implicitly_wait(5)
        ActionChains(driver).move_to_element(button).click(button).perform()
    except:
        print("No accept button")
    # ============== show all funds ==================
    try:
        button = driver.find_element_by_class_name(u"mod_flexible_sidebar_cta_button")
        driver.implicitly_wait(random.uniform(1, 3))
        ActionChains(driver).move_to_element(button).click(button).perform()
    except:
        print("No show all button")
    read_links(country_name)

final_df = pd.concat(df_list)
final_df.to_csv('Data/combined_data.csv', index=False)
dedupe_df = final_df.drop_duplicates(['Fund name','AUM'],keep='first')
dedupe_df.to_csv('Data/CS_Data.csv', index=False)
