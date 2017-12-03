# -*- coding: utf-8 -*-
__author = 'dobby'

from selenium.webdriver.common.action_chains            import ActionChains
from selenium.webdriver.common.by                       import By
from selenium.common.exceptions                         import TimeoutException
from selenium                                           import webdriver
from mooc_item                                          import DataItem
import selenium.webdriver.support.expected_conditions   as EC
import selenium.webdriver.support.ui                    as ui
import simplejson                                       as json
import requests
import time
import config


#------------------------short name config----------------------------
cid = config.CID
domain = config.DOMAIN_NAME
core = config.CORE_TIME


class AutoHandlerVideo(object):
    """
        Poor word bla, hope U good luck.
    """

    def __init__(self):
        self.class_count = 0
        self.less_count = 0
        self.data_items = []
        self.elements = {
                        'account_text': '#account',
                        'passwd_text': '#password',
                        'login_btn': '.btn',
                        'move_right': '.handler',
                        'login_succeed':'#top_avatar'
                        }
        self.session = requests.Session()
        self.session.headers = config.HEADERS
        self.driver = webdriver.Firefox(log_path='/temp/geckodriver.log')
        self.login_mooc_page()
        self.add_obItems()


    def is_visible(self, locator, timeout=15):
        """
        judge that element's visible
        :return: boolen
        """
        try:
            ui.WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, locator)))
            return True
        except TimeoutException:
            return False


    def find_element(self, selector):
        """
        short func find element, way to CSSseletor search
        """
        return self.driver.find_element_by_css_selector(selector)


    def login_mooc_page(self):
        """
        login action
        """
        self.driver.get('{domain}/user/login'.format(domain=domain))
        if self.is_visible(self.elements['account_text']):
            self.find_element(self.elements['account_text']).send_keys(config.USER_NAME)
            self.find_element(self.elements['passwd_text']).send_keys(config.PASS_WORD)
            # move progress to right
            sliter = self.find_element(self.elements['move_right'])
            ActionChains(self.driver).click_and_hold(on_element=sliter).perform()
            ActionChains(self.driver).move_to_element_with_offset(to_element=sliter, xoffset=750, yoffset=300).perform()
            time.sleep(5)
            # delay login action
            self.find_element(self.elements['login_btn']).click()


    def set_session_cookie(self):
        """
        cookie transplant to session
        """
        self.driver.get('{domain}/home/learn/index#/{cid}/go'.format(domain=domain,cid=cid))
        for subCookie in self.driver.get_cookies():
            self.session.cookies.set(subCookie[u'name'], self.driver.get_cookie(subCookie[u'name'])['value'])
        if config.DEBUG:
            print "session cookies :: \n{}".format(self.session.cookies)


    def add_obItems(self):
        """
        calculator how many class
                and
        how many should handler
        """
        self.set_session_cookie()
        api_data = self.session.get(
            '{domain}/home/learn/getCatalogList?cid={cid}&hidemsg_=true&show='.format(domain=domain,cid=cid))
        if config.DEBUG:
            print "api_data.url :: \n{url}, content ::\n{content}". \
                  format(url=api_data.url, content=api_data.content)
        chapter_list = json.loads(api_data.content)['data']

        for subChapter in chapter_list:
            self.class_count += len(subChapter['children'])
            for subItem in subChapter['children']:
                dataItem = DataItem()
                dataItem.chapter = subChapter['id']
                dataItem.catalog = subItem['id']
                dataItem.section = subItem['id']
                self.data_items.append(dataItem)
                if int(subItem['finished']) == 0:
                    self.less_count += 1
        print 'message show: has all class count = {count}, and should handler has {less}'.\
                                        format(count=self.class_count, less=self.less_count)


if __name__ == '__main__':
    autoArch = AutoHandlerVideo()

    print '-----------------------------------it\'s start short-------------------------------------------------'
    for index in xrange(autoArch.class_count):
        print 'current index: __{}__:'.format(index)
        dataItem = autoArch.data_items[index]
        resp = autoArch.session.get('{domain}/home/learn/getCourseLearn?cid={cid}'.format(domain=domain,cid=cid))
        video_info = json.loads(resp.content)['data']
        # each section must be refresh, to fetch section ID true
        more_one_section = autoArch.session.get('{domain}/home/learn/getUnitLearn?\
                                        catalog_id={section_id_1}\
                                        &chapter_id={chapter_id}\
                                        &cid={cid}\
                                        &hidemsg_=true\
                                        &section_id={section_id_2}\
                                        &show='.format(domain=domain,section_id_1=video_info['subsection_id'],
                                                       chapter_id=dataItem.chapter,cid=cid,section_id_2=dataItem.section))
        ##
            #maybe here will show u error. yet, but it's working after i finish the first classVideo , hope u do that this way if u meet...
        ##
        if config.DEBUG:
            print "more_one_section.url :: \n{url}, content ::\n{content}". \
                  format(url=more_one_section.url, content=more_one_section.content)

        section_list = json.loads(more_one_section.content)['data']
        for subSection in section_list:
            resource_id = subSection['id']

            payload = {
                'chapter_id':dataItem.chapter,
                'section_id':dataItem.section,
                'subsection_id':video_info['subsection_id'],
                'resource_id':resource_id,
                'source':'1',
                'network':'2',
                'hidemsg':'true',
                'cid':'{cid}'.format(cid=cid),
                'video_length':'{}'.format(core),
                'video_pos':'{}'.format(core)
            }

            response = autoArch.session.post('{domain}/home/learn/markVideoLearn'.format(domain=domain),data=payload)
            if config.DEBUG:
                print "response post.url ::\n{url}, content ::\n{content}, payload ::\n{payload}".\
                                format(url=response.url, content=response.content, payload=payload)
            result = json.loads(response.content)
            if int(result['code']) == 1:
                print result
                print '--------------------------------{}->-succeed-----------------------------------'.format(resource_id)
            else:
                print '--------------------------------{id}->Error:{error}----------'.format(id=resource_id,error=result['msg'])

