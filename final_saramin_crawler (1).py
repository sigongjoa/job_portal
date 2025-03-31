#!/usr/bin/env python3
"""
최종 사람인 크롤러 - 근무조건 추출 개선
"""

import time
import logging
import json
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalSaraminCrawler:
    """최종 사람인 크롤러 클래스"""
    
    def __init__(self):
        self.site_name = "Saramin"
        self.data = []
        self.max_retries = 3
        self.wait_time = 30
        
    def setup_driver(self):
        """Selenium 웹드라이버 설정"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    
    def crawl_job_list(self, url, max_jobs=None):
        """채용 공고 목록 페이지에서 채용 공고 URL 추출"""
        logger.info(f"크롤링 시작: {url}")
        
        for retry in range(self.max_retries):
            try:
                driver = self.setup_driver()
                driver.get(url)
                
                # 페이지 로딩 대기
                logger.info(f"페이지 로딩 대기 중... ({self.wait_time}초)")
                time.sleep(self.wait_time)
                
                # 채용 공고 URL 추출
                job_urls = []
                
                # 다양한 선택자 시도
                selectors = [
                    '.item_recruit',
                    '.list_item',
                    '.list_recruit',
                    '.jobsearch-result-list',
                    '.content-section.jobs-content',
                    '.list_jobs',
                    '.list_product',
                    '.recruit_list',
                    '.recruit-info',
                    '.job-list',
                    '.job_list',
                    '.list-positions'
                ]
                
                for selector in selectors:
                    try:
                        job_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        logger.info(f"선택자 '{selector}'로 {len(job_elements)}개 요소 찾음")
                        
                        if job_elements:
                            for job in job_elements:
                                try:
                                    # 다양한 링크 선택자 시도
                                    link_selectors = [
                                        'h2.job_tit a',
                                        'a.job_link',
                                        'a[href*="jobs"]',
                                        'a'  # 마지막 시도로 모든 링크 검색
                                    ]
                                    
                                    for link_selector in link_selectors:
                                        try:
                                            link_elements = job.find_elements(By.CSS_SELECTOR, link_selector)
                                            if link_elements:
                                                for link in link_elements:
                                                    job_url = link.get_attribute('href')
                                                    if job_url and 'saramin.co.kr' in job_url and 'jobs' in job_url and 'view' in job_url:
                                                        if job_url not in job_urls:
                                                            logger.info(f"채용 공고 URL 찾음: {job_url}")
                                                            job_urls.append(job_url)
                                                break  # 링크를 찾았으면 다음 링크 선택자 시도 중단
                                        except Exception as e:
                                            logger.warning(f"링크 선택자 '{link_selector}' 시도 중 오류: {e}")
                                except Exception as e:
                                    logger.warning(f"채용 공고 URL 추출 중 오류 발생: {e}")
                            
                            if job_urls:
                                break  # URL을 찾았으면 다음 선택자 시도 중단
                    except Exception as e:
                        logger.warning(f"선택자 '{selector}' 시도 중 오류: {e}")
                
                # 직접 모든 링크 검색 (마지막 시도)
                if not job_urls:
                    logger.info("모든 링크 직접 검색 시도")
                    all_links = driver.find_elements(By.TAG_NAME, 'a')
                    logger.info(f"총 {len(all_links)}개 링크 요소 찾음")
                    
                    for link in all_links:
                        try:
                            href = link.get_attribute('href')
                            if href and 'saramin.co.kr' in href and 'jobs' in href and 'view' in href:
                                if href not in job_urls:
                                    logger.info(f"채용 공고 URL 찾음 (직접 검색): {href}")
                                    job_urls.append(href)
                        except Exception as e:
                            continue  # 오류 발생 시 다음 링크로 진행
                
                logger.info(f"총 {len(job_urls)}개의 채용 공고 URL을 찾았습니다.")
                
                # 최대 크롤링할 채용 공고 수 제한
                if max_jobs and max_jobs < len(job_urls):
                    logger.info(f"최대 {max_jobs}개의 채용 공고만 크롤링합니다.")
                    job_urls = job_urls[:max_jobs]
                
                # 테스트용 URL 추가 (실제 URL을 찾지 못한 경우)
                if not job_urls:
                    logger.warning("실제 URL을 찾지 못했습니다. 테스트용 URL을 사용합니다.")
                    test_urls = [
                        "https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=50157673&recommend_ids=eJxNj7kVA0EIQ6txDgIExC5k%2B%2B%2FCjO2d2fA%2FoYMQMRC4SvWV7xDAsutqwRc1CF8qB728vcGD9Ko8XtHK%2FKvjRVjEIzk1uZOnqKQ32uzovpO7oii3dzqLyN5RUyONXYRgUvdxMQJx1HTttUp%2BSIGdf00tPZ6bg3285U5bxx8%2BFkAK&view_type=list&gz=1&t_ref_content=section_favor_001&t_ref=area_recruit&t_ref_area=101&relayNonce=815ea571f5228eaed777&immediately_apply_layer_open=n#seq=1"
                    ]
                    job_urls = test_urls
                
                driver.quit()
                return job_urls
            
            except Exception as e:
                logger.error(f"채용 공고 목록 크롤링 중 오류 발생 (시도 {retry+1}/{self.max_retries}): {e}")
                if driver:
                    driver.quit()
                
                if retry < self.max_retries - 1:
                    logger.info(f"{5 * (retry + 1)}초 후 재시도합니다...")
                    time.sleep(5 * (retry + 1))
                else:
                    logger.error("최대 재시도 횟수를 초과했습니다.")
                    return []
    
    def extract_text_safely(self, driver, selector, multiple=False):
        """안전하게 텍스트 추출"""
        try:
            if multiple:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                return [element.text.strip() for element in elements if element.text.strip()]
            else:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                return element.text.strip()
        except Exception as e:
            return [] if multiple else ""
    
    def extract_with_multiple_selectors(self, driver, selectors, multiple=False):
        """여러 선택자를 시도하여 텍스트 추출"""
        for selector in selectors:
            try:
                result = self.extract_text_safely(driver, selector, multiple)
                if result:
                    logger.info(f"선택자 '{selector}'로 데이터 추출 성공")
                    return result
            except Exception as e:
                continue
        return [] if multiple else ""
    
    def extract_table_data(self, driver, table_selector):
        """테이블 데이터 추출"""
        try:
            tables = driver.find_elements(By.CSS_SELECTOR, table_selector)
            if not tables:
                return {}
            
            table_data = {}
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, 'tr')
                for row in rows:
                    try:
                        th_elements = row.find_elements(By.TAG_NAME, 'th')
                        td_elements = row.find_elements(By.TAG_NAME, 'td')
                        
                        if th_elements and td_elements:
                            key = th_elements[0].text.strip()
                            value = td_elements[0].text.strip()
                            if key and value:
                                table_data[key] = value
                    except Exception as e:
                        continue
            
            return table_data
        except Exception as e:
            logger.warning(f"테이블 데이터 추출 중 오류 발생: {e}")
            return {}
    
    def extract_job_conditions(self, driver):
        """근무조건 추출 - 개선된 버전"""
        conditions = {}
        
        # 1. 근무조건 섹션 찾기 (가장 정확한 방법)
        try:
            condition_sections = driver.find_elements(By.CSS_SELECTOR, '.jv_cont')
            for section in condition_sections:
                try:
                    title_element = section.find_element(By.CSS_SELECTOR, '.tit_job_condition')
                    title = title_element.text.strip()
                    if '근무조건' in title:
                        logger.info(f"근무조건 섹션 찾음: {title}")
                        items = section.find_elements(By.CSS_SELECTOR, '.cont .item')
                        for item in items:
                            try:
                                dt = item.find_element(By.CSS_SELECTOR, 'dt').text.strip()
                                dd = item.find_element(By.CSS_SELECTOR, 'dd').text.strip()
                                if dt and dd:
                                    conditions[dt] = dd
                                    logger.info(f"근무조건 항목: {dt} - {dd}")
                            except Exception as e:
                                continue
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"근무조건 섹션 찾기 중 오류 발생: {e}")
        
        # 2. 상세 정보 테이블 찾기
        try:
            info_tables = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info')
            for table in info_tables:
                try:
                    rows = table.find_elements(By.CSS_SELECTOR, 'div.row')
                    for row in rows:
                        try:
                            dt = row.find_element(By.CSS_SELECTOR, 'div.col.head').text.strip()
                            dd = row.find_element(By.CSS_SELECTOR, 'div.col.body').text.strip()
                            if dt and dd:
                                conditions[dt] = dd
                                logger.info(f"상세 정보 항목: {dt} - {dd}")
                        except Exception as e:
                            continue
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"상세 정보 테이블 찾기 중 오류 발생: {e}")
        
        # 3. 특정 필드 직접 찾기
        field_selectors = {
            '경력': ['.experience', '.career', '.info_exp', '#job-position-job-experience-text'],
            '학력': ['.education', '.info_edu', '#job-position-job-education-text'],
            '근무형태': ['.employment_type', '.info_emp_type', '#job-position-job-type-text'],
            '근무지역': ['.location', '.info_loc', '#job-position-job-location-text', '.work_place'],
            '근무시간': ['.work_time', '.info_work_time', '#job-position-job-worktime-text'],
            '급여': ['.salary', '.info_salary', '#job-position-job-salary-text']
        }
        
        for field, selectors in field_selectors.items():
            if field not in conditions:  # 이미 찾은 필드는 건너뛰기
                value = self.extract_with_multiple_selectors(driver, selectors)
                if value:
                    conditions[field] = value
                    logger.info(f"직접 찾은 {field}: {value}")
        
        # 4. 페이지 소스에서 정규식으로 찾기
        if not conditions:
            try:
                page_source = driver.page_source
                
                # 경력 패턴
                career_patterns = [
                    r'경력\s*[:：]\s*([^<\n]+)',
                    r'경력</dt>\s*<dd[^>]*>([^<]+)',
                    r'경력\s*</th>\s*<td[^>]*>([^<]+)'
                ]
                
                for pattern in career_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['경력'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 경력: {conditions['경력']}")
                        break
                
                # 학력 패턴
                education_patterns = [
                    r'학력\s*[:：]\s*([^<\n]+)',
                    r'학력</dt>\s*<dd[^>]*>([^<]+)',
                    r'학력\s*</th>\s*<td[^>]*>([^<]+)'
                ]
                
                for pattern in education_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['학력'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 학력: {conditions['학력']}")
                        break
                
                # 근무지역 패턴
                location_patterns = [
                    r'근무지역\s*[:：]\s*([^<\n]+)',
                    r'근무지</dt>\s*<dd[^>]*>([^<]+)',
                    r'근무지\s*</th>\s*<td[^>]*>([^<]+)',
                    r'지역\s*[:：]\s*([^<\n]+)'
                ]
                
                for pattern in location_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['근무지역'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 근무지역: {conditions['근무지역']}")
                        break
                
                # 고용형태 패턴
                employment_patterns = [
                    r'고용형태\s*[:：]\s*([^<\n]+)',
                    r'고용형태</dt>\s*<dd[^>]*>([^<]+)',
                    r'고용형태\s*</th>\s*<td[^>]*>([^<]+)',
                    r'근무형태\s*[:：]\s*([^<\n]+)'
                ]
                
                for pattern in employment_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['고용형태'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 고용형태: {conditions['고용형태']}")
                        break
                
                # 급여 패턴
                salary_patterns = [
                    r'급여\s*[:：]\s*([^<\n]+)',
                    r'급여</dt>\s*<dd[^>]*>([^<]+)',
                    r'급여\s*</th>\s*<td[^>]*>([^<]+)',
                    r'연봉\s*[:：]\s*([^<\n]+)'
                ]
                
                for pattern in salary_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['급여'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 급여: {conditions['급여']}")
                        break
            except Exception as e:
                logger.warning(f"정규식 검색 중 오류 발생: {e}")
        
        # 5. 이미지 분석 (사용자가 제공한 이미지 참고)
        # 이미지에서 본 구조를 기반으로 직접 추출
        try:
            # 경력
            career_elements = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info .row')
            for element in career_elements:
                try:
                    head = element.find_element(By.CSS_SELECTOR, '.col.head').text.strip()
                    if '경력' in head:
                        body = element.find_element(By.CSS_SELECTOR, '.col.body').text.strip()
                        conditions['경력'] = body
                        logger.info(f"이미지 구조 기반으로 찾은 경력: {body}")
                except Exception as e:
                    continue
            
            # 학력
            education_elements = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info .row')
            for element in education_elements:
                try:
                    head = element.find_element(By.CSS_SELECTOR, '.col.head').text.strip()
                    if '학력' in head:
                        body = element.find_element(By.CSS_SELECTOR, '.col.body').text.strip()
                        conditions['학력'] = body
                        logger.info(f"이미지 구조 기반으로 찾은 학력: {body}")
                except Exception as e:
                    continue
            
            # 근무형태
            employment_elements = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info .row')
            for element in employment_elements:
                try:
                    head = element.find_element(By.CSS_SELECTOR, '.col.head').text.strip()
                    if '근무형태' in head:
                        body = element.find_element(By.CSS_SELECTOR, '.col.body').text.strip()
                        conditions['근무형태'] = body
                        logger.info(f"이미지 구조 기반으로 찾은 근무형태: {body}")
                except Exception as e:
                    continue
            
            # 근무지역
            location_elements = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info .row')
            for element in location_elements:
                try:
                    head = element.find_element(By.CSS_SELECTOR, '.col.head').text.strip()
                    if '근무지역' in head:
                        body = element.find_element(By.CSS_SELECTOR, '.col.body').text.strip()
                        conditions['근무지역'] = body
                        logger.info(f"이미지 구조 기반으로 찾은 근무지역: {body}")
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"이미지 구조 기반 추출 중 오류 발생: {e}")
        
        return conditions
    
    def extract_welfare_benefits(self, driver):
        """복리후생 추출"""
        try:
            welfare_sections = driver.find_elements(By.CSS_SELECTOR, '.jv_cont')
            for section in welfare_sections:
                try:
                    title = section.find_element(By.CSS_SELECTOR, '.tit_job_condition').text.strip()
                    if '복리후생' in title:
                        content = section.find_element(By.CSS_SELECTOR, '.cont').text.strip()
                        return content
                except Exception as e:
                    continue
            
            # 다른 선택자 시도
            welfare_selectors = [
                '.welfare',
                '.benefits',
                '#job-welfare-text',
                '.jv_benefit'
            ]
            
            welfare = self.extract_with_multiple_selectors(driver, welfare_selectors)
            return welfare
        except Exception as e:
            logger.warning(f"복리후생 추출 중 오류 발생: {e}")
            return ""
    
    def extract_application_period(self, driver):
        """접수기간 및 방법 추출"""
        application_info = {}
        
        try:
            # 접수기간 및 방법 섹션 찾기
            application_sections = driver.find_elements(By.CSS_SELECTOR, '.jv_cont')
            for section in application_sections:
                try:
                    title = section.find_element(By.CSS_SELECTOR, '.tit_job_condition').text.strip()
                    if '접수기간' in title or '지원방법' in title:
                        items = section.find_elements(By.CSS_SELECTOR, '.cont .item')
                        for item in items:
                            try:
                                dt = item.find_element(By.CSS_SELECTOR, 'dt').text.strip()
                                dd = item.find_element(By.CSS_SELECTOR, 'dd').text.strip()
                                if dt and dd:
                                    application_info[dt] = dd
                            except Exception as e:
                                continue
                except Exception as e:
                    continue
            
            # 직접 선택자 시도
            deadline_selectors = [
                '.deadline',
                '.apply_deadline',
                '#job-application-deadline-text',
                '.info_period'
            ]
            
            deadline = self.extract_with_multiple_selectors(driver, deadline_selectors)
            if deadline:
                application_info['접수기간'] = deadline
            
            method_selectors = [
                '.apply_method',
                '.application_method',
                '#job-application-method-text',
                '.info_apply'
            ]
            
            method = self.extract_with_multiple_selectors(driver, method_selectors)
            if method:
                application_info['지원방법'] = method
        except Exception as e:
            logger.warning(f"접수기간 및 방법 추출 중 오류 발생: {e}")
        
        return application_info
    
    def extract_company_info(self, driver):
        """기업정보 추출"""
        company_info = {}
        
        try:
            # 기업정보 섹션 찾기
            company_sections = driver.find_elements(By.CSS_SELECTOR, '.jv_cont')
            for section in company_sections:
                try:
                    title = section.find_element(By.CSS_SELECTOR, '.tit_job_condition').text.strip()
                    if '기업정보' in title:
                        items = section.find_elements(By.CSS_SELECTOR, '.cont .item')
                        for item in items:
                            try:
                                dt = item.find_element(By.CSS_SELECTOR, 'dt').text.strip()
                                dd = item.find_element(By.CSS_SELECTOR, 'dd').text.strip()
                                if dt and dd:
                                    company_info[dt] = dd
                            except Exception as e:
                                continue
                except Exception as e:
                    continue
            
            # 직접 선택자 시도
            company_name_selectors = [
                '.company_name',
                '.corp_name',
                '#company-name-text',
                '.info_company'
            ]
            
            company_name = self.extract_with_multiple_selectors(driver, company_name_selectors)
            if company_name:
                company_info['회사명'] = company_name
            
            company_type_selectors = [
                '.company_type',
                '.corp_type',
                '#company-type-text',
                '.info_company_type'
            ]
            
            company_type = self.extract_with_multiple_selectors(driver, company_type_selectors)
            if company_type:
                company_info['기업형태'] = company_type
            
            company_size_selectors = [
                '.company_size',
                '.corp_size',
                '#company-size-text',
                '.info_company_size'
            ]
            
            company_size = self.extract_with_multiple_selectors(driver, company_size_selectors)
            if company_size:
                company_info['기업규모'] = company_size
            
            company_industry_selectors = [
                '.company_industry',
                '.corp_industry',
                '#company-industry-text',
                '.info_company_industry'
            ]
            
            company_industry = self.extract_with_multiple_selectors(driver, company_industry_selectors)
            if company_industry:
                company_info['산업'] = company_industry
        except Exception as e:
            logger.warning(f"기업정보 추출 중 오류 발생: {e}")
        
        return company_info
    
    def crawl_job_detail(self, url):
        """채용 공고 상세 페이지에서 정보 추출"""
        logger.info(f"채용 공고 크롤링 중: {url}")
        
        for retry in range(self.max_retries):
            try:
                driver = self.setup_driver()
                driver.get(url)
                
                # 페이지 로딩 대기
                logger.info(f"페이지 로딩 대기 중... ({self.wait_time}초)")
                time.sleep(self.wait_time)
                
                # 기본 정보 초기화
                job_data = {
                    'site': self.site_name,
                    'url': url,
                    'company_name': '',
                    'title': '',
                    'deadline': '',
                    'location': '',
                    'experience': '',
                    'education': '',
                    'employment_type': '',
                    'salary': '',
                    'description': '',
                    'welfare_benefits': '',
                    'application_period': {},
                    'company_info': {}
                }
                
                # 회사명 추출
                company_name_selectors = [
                    '.company_name',
                    '.corp_name',
                    '.name',
                    'a[href*="company"]',
                    'a[href*="corp"]',
                    '.company',
                    '.corp',
                    '#company_name',
                    '#corp_name',
                    '.jv_header .company_name',
                    '.jv_company .name'
                ]
                
                company_name = self.extract_with_multiple_selectors(driver, company_name_selectors)
                if company_name:
                    job_data['company_name'] = company_name
                    logger.info(f"회사명: {company_name}")
                
                # 공고 제목 추출
                title_selectors = [
                    '.tit_job',
                    '.recruit_title',
                    '.job_tit',
                    'h1',
                    'h2',
                    '.title',
                    '.job_title',
                    '#job_title',
                    '.header_top_title',
                    '.jv_header .tit_job',
                    '.jv_title'
                ]
                
                title = self.extract_with_multiple_selectors(driver, title_selectors)
                if title:
                    job_data['title'] = title
                    logger.info(f"공고 제목: {title}")
                
                # 근무조건 추출 (개선된 버전)
                job_conditions = self.extract_job_conditions(driver)
                logger.info(f"근무조건: {job_conditions}")
                
                if '경력' in job_conditions:
                    job_data['experience'] = job_conditions['경력']
                
                if '학력' in job_conditions:
                    job_data['education'] = job_conditions['학력']
                
                if '근무형태' in job_conditions:
                    job_data['employment_type'] = job_conditions['근무형태']
                elif '고용형태' in job_conditions:
                    job_data['employment_type'] = job_conditions['고용형태']
                
                if '근무지역' in job_conditions:
                    job_data['location'] = job_conditions['근무지역']
                elif '근무지' in job_conditions:
                    job_data['location'] = job_conditions['근무지']
                
                if '급여' in job_conditions:
                    job_data['salary'] = job_conditions['급여']
                elif '연봉' in job_conditions:
                    job_data['salary'] = job_conditions['연봉']
                
                # 복리후생 추출
                welfare_benefits = self.extract_welfare_benefits(driver)
                if welfare_benefits:
                    job_data['welfare_benefits'] = welfare_benefits
                    logger.info(f"복리후생: {welfare_benefits[:100]}...")
                
                # 접수기간 및 방법 추출
                application_period = self.extract_application_period(driver)
                if application_period:
                    job_data['application_period'] = application_period
                    logger.info(f"접수기간 및 방법: {application_period}")
                    
                    if '접수기간' in application_period:
                        job_data['deadline'] = application_period['접수기간']
                
                # 기업정보 추출
                company_info = self.extract_company_info(driver)
                if company_info:
                    job_data['company_info'] = company_info
                    logger.info(f"기업정보: {company_info}")
                
                # 상세 내용 추출
                description_selectors = [
                    '#job_content',
                    '.job_detail_content',
                    '.recruit_detail',
                    '.job_detail',
                    '.detail_content',
                    '#jobDescriptionContent',
                    '.job_description',
                    '.description',
                    '.detail',
                    '.content',
                    '.jv_detail',
                    '.jv_cont .desc',
                    '.jv_cont .cont'
                ]
                
                description = self.extract_with_multiple_selectors(driver, description_selectors)
                if description:
                    job_data['description'] = description
                    logger.info(f"상세 내용 길이: {len(description)} 자")
                
                # 데이터 검증
                for key, value in job_data.items():
                    if key not in ['site', 'url', 'welfare_benefits', 'application_period', 'company_info', 'description'] and not value:
                        logger.warning(f"{key} 정보를 찾을 수 없습니다.")
                
                logger.info("채용 공고 크롤링 완료")
                driver.quit()
                return job_data
            
            except Exception as e:
                logger.error(f"채용 공고 상세 페이지 크롤링 중 오류 발생 (시도 {retry+1}/{self.max_retries}): {e}")
                if driver:
                    driver.quit()
                
                if retry < self.max_retries - 1:
                    logger.info(f"{5 * (retry + 1)}초 후 재시도합니다...")
                    time.sleep(5 * (retry + 1))
                else:
                    logger.error("최대 재시도 횟수를 초과했습니다.")
                    return None
    
    def crawl(self, url, max_jobs=None):
        """URL에서 채용 공고 크롤링"""
        job_urls = self.crawl_job_list(url, max_jobs)
        
        results = []
        for job_url in job_urls:
            job_data = self.crawl_job_detail(job_url)
            if job_data:
                results.append(job_data)
        
        self.data = results
        logger.info(f"크롤링 완료: 총 {len(results)}개의 채용 공고를 수집했습니다.")
        
        return results
    
    def save_to_csv(self, filename):
        """수집한 데이터를 CSV 파일로 저장"""
        if not self.data:
            logger.warning("저장할 데이터가 없습니다.")
            return None
        
        # 중첩된 딕셔너리 처리
        flattened_data = []
        for item in self.data:
            flat_item = item.copy()
            
            # 중첩된 딕셔너리를 문자열로 변환
            for key in ['application_period', 'company_info']:
                if key in flat_item and isinstance(flat_item[key], dict):
                    flat_item[key] = json.dumps(flat_item[key], ensure_ascii=False)
            
            flattened_data.append(flat_item)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        logger.info(f"데이터가 성공적으로 저장되었습니다: {filename}")
        return filename
    
    def save_to_json(self, filename):
        """수집한 데이터를 JSON 파일로 저장"""
        if not self.data:
            logger.warning("저장할 데이터가 없습니다.")
            return None
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"데이터가 성공적으로 저장되었습니다: {filename}")
        return filename


def test_final_crawler():
    """최종 크롤러 테스트"""
    print("=" * 80)
    print("최종 사람인 크롤러 테스트 시작")
    print("=" * 80)
    
    # 크롤러 인스턴스 생성
    crawler = FinalSaraminCrawler()
    
    # 테스트 URL
    url = 'https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=개발자'
    
    # 특정 URL 테스트
    specific_url = "https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=50157673&recommend_ids=eJxNj7kVA0EIQ6txDgIExC5k%2B%2B%2FCjO2d2fA%2FoYMQMRC4SvWV7xDAsutqwRc1CF8qB728vcGD9Ko8XtHK%2FKvjRVjEIzk1uZOnqKQ32uzovpO7oii3dzqLyN5RUyONXYRgUvdxMQJx1HTttUp%2BSIGdf00tPZ6bg3285U5bxx8%2BFkAK&view_type=list&gz=1&t_ref_content=section_favor_001&t_ref=area_recruit&t_ref_area=101&relayNonce=815ea571f5228eaed777&immediately_apply_layer_open=n#seq=1"
    
    # 특정 URL만 테스트
    print(f"\n특정 URL 테스트: {specific_url}")
    job_data = crawler.crawl_job_detail(specific_url)
    
    if job_data:
        print("\n[크롤링 결과]")
        print(f"회사명: {job_data.get('company_name', '정보 없음')}")
        print(f"공고 제목: {job_data.get('title', '정보 없음')}")
        print(f"마감일: {job_data.get('deadline', '정보 없음')}")
        print(f"근무지: {job_data.get('location', '정보 없음')}")
        print(f"경력: {job_data.get('experience', '정보 없음')}")
        print(f"학력: {job_data.get('education', '정보 없음')}")
        print(f"고용형태: {job_data.get('employment_type', '정보 없음')}")
        print(f"급여: {job_data.get('salary', '정보 없음')}")
        
        print("\n복리후생:")
        print(job_data.get('welfare_benefits', '정보 없음'))
        
        print("\n접수기간 및 방법:")
        for key, value in job_data.get('application_period', {}).items():
            print(f"  {key}: {value}")
        
        print("\n기업정보:")
        for key, value in job_data.get('company_info', {}).items():
            print(f"  {key}: {value}")
        
        desc = job_data.get('description', '')
        if desc:
            print(f"\n상세 내용 (일부): {desc[:200]}...")
        else:
            print("\n상세 내용: 정보 없음")
        
        # JSON 파일로 저장
        crawler.data = [job_data]
        json_file = crawler.save_to_json("final_saramin_job.json")
        print(f"\n결과가 {json_file} 파일에 저장되었습니다.")
    
    # 일반 검색 URL 테스트 (최대 2개 채용 공고만 크롤링)
    print(f"\n일반 검색 URL 테스트: {url}")
    results = crawler.crawl(url, max_jobs=2)
    
    # 결과 출력
    print("\n[크롤링 결과]")
    print(f"총 {len(results)}개의 채용 공고를 크롤링했습니다.")
    
    for i, job in enumerate(results):
        print(f"\n채용 공고 {i+1}:")
        print(f"  회사명: {job.get('company_name', '정보 없음')}")
        print(f"  공고 제목: {job.get('title', '정보 없음')}")
        print(f"  마감일: {job.get('deadline', '정보 없음')}")
        print(f"  근무지: {job.get('location', '정보 없음')}")
        print(f"  경력: {job.get('experience', '정보 없음')}")
        print(f"  학력: {job.get('education', '정보 없음')}")
        print(f"  고용형태: {job.get('employment_type', '정보 없음')}")
        print(f"  급여: {job.get('salary', '정보 없음')}")
        
        print("\n  복리후생:")
        print(f"    {job.get('welfare_benefits', '정보 없음')[:100]}...")
        
        print("\n  접수기간 및 방법:")
        for key, value in job.get('application_period', {}).items():
            print(f"    {key}: {value}")
        
        print("\n  기업정보:")
        for key, value in job.get('company_info', {}).items():
            print(f"    {key}: {value}")
        
        desc = job.get('description', '')
        if desc:
            print(f"\n  상세 내용 (일부): {desc[:200]}...")
        else:
            print("\n  상세 내용: 정보 없음")
    
    # CSV 파일로 저장
    csv_file = crawler.save_to_csv("final_saramin_jobs.csv")
    print(f"\n결과가 {csv_file} 파일에 저장되었습니다.")
    
    # JSON 파일로 저장
    json_file = crawler.save_to_json("final_saramin_jobs.json")
    print(f"\n결과가 {json_file} 파일에 저장되었습니다.")
    
    print("=" * 80)
    print("테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    test_final_crawler()
