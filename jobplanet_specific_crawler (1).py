#!/usr/bin/env python3
"""
잡플래닛 채용공고 크롤러 - 특정 URL에서 요약 정보, 주요 업무, 자격 요건, 회사 위치 정보만 추출
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

class JobPlanetCrawler:
    """잡플래닛 채용공고 크롤러 클래스"""
    
    def __init__(self):
        self.site_name = "JobPlanet"
        self.data = {}
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
            logger.warning(f"선택자 '{selector}'로 텍스트 추출 실패: {e}")
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
    
    def extract_summary_info(self, driver):
        """요약 정보 추출"""
        summary_info = {}
        
        # 요약 정보 섹션 찾기
        summary_selectors = [
            '.jp-jobs-detail-summary',
            '.job-summary',
            '.summary-section',
            '.job-detail-summary',
            '.job-posting-summary',
            '.summary-info'
        ]
        
        # 마감일
        deadline_selectors = [
            '.jp-jobs-detail-summary .deadline',
            '.job-summary .deadline',
            '.summary-section .deadline',
            '.deadline',
            '.due-date',
            '.job-deadline',
            '.jp-jobs-detail-summary-item:contains("마감일")',
            '[data-test="deadline"]'
        ]
        
        deadline = self.extract_with_multiple_selectors(driver, deadline_selectors)
        if deadline:
            summary_info['마감일'] = deadline
        
        # 직무
        job_role_selectors = [
            '.jp-jobs-detail-summary .job-role',
            '.job-summary .job-role',
            '.summary-section .job-role',
            '.job-role',
            '.position',
            '.job-position',
            '.jp-jobs-detail-summary-item:contains("직무")',
            '[data-test="job-role"]'
        ]
        
        job_role = self.extract_with_multiple_selectors(driver, job_role_selectors)
        if job_role:
            summary_info['직무'] = job_role
        
        # 경력
        experience_selectors = [
            '.jp-jobs-detail-summary .experience',
            '.job-summary .experience',
            '.summary-section .experience',
            '.experience',
            '.career',
            '.job-experience',
            '.jp-jobs-detail-summary-item:contains("경력")',
            '[data-test="experience"]'
        ]
        
        experience = self.extract_with_multiple_selectors(driver, experience_selectors)
        if experience:
            summary_info['경력'] = experience
        
        # 고용형태
        employment_type_selectors = [
            '.jp-jobs-detail-summary .employment-type',
            '.job-summary .employment-type',
            '.summary-section .employment-type',
            '.employment-type',
            '.job-type',
            '.employment',
            '.jp-jobs-detail-summary-item:contains("고용형태")',
            '[data-test="employment-type"]'
        ]
        
        employment_type = self.extract_with_multiple_selectors(driver, employment_type_selectors)
        if employment_type:
            summary_info['고용형태'] = employment_type
        
        # 근무지역
        location_selectors = [
            '.jp-jobs-detail-summary .location',
            '.job-summary .location',
            '.summary-section .location',
            '.location',
            '.work-location',
            '.job-location',
            '.jp-jobs-detail-summary-item:contains("근무지역")',
            '[data-test="location"]'
        ]
        
        location = self.extract_with_multiple_selectors(driver, location_selectors)
        if location:
            summary_info['근무지역'] = location
        
        # 스킬
        skills_selectors = [
            '.jp-jobs-detail-summary .skills',
            '.job-summary .skills',
            '.summary-section .skills',
            '.skills',
            '.required-skills',
            '.job-skills',
            '.jp-jobs-detail-summary-item:contains("스킬")',
            '[data-test="skills"]'
        ]
        
        skills = self.extract_with_multiple_selectors(driver, skills_selectors)
        if skills:
            summary_info['스킬'] = skills
        
        # 페이지 소스에서 정규식으로 찾기
        if not summary_info:
            try:
                page_source = driver.page_source
                
                # 마감일 패턴
                deadline_patterns = [
                    r'마감일\s*[:：]\s*([^<\n]+)',
                    r'마감일</dt>\s*<dd[^>]*>([^<]+)',
                    r'마감일\s*</th>\s*<td[^>]*>([^<]+)',
                    r'D-(\d+)',
                    r'(\d{4}[./-]\d{2}[./-]\d{2})\s*D-\d+'
                ]
                
                for pattern in deadline_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        summary_info['마감일'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 마감일: {summary_info['마감일']}")
                        break
                
                # 직무 패턴
                job_role_patterns = [
                    r'직무\s*[:：]\s*([^<\n]+)',
                    r'직무</dt>\s*<dd[^>]*>([^<]+)',
                    r'직무\s*</th>\s*<td[^>]*>([^<]+)'
                ]
                
                for pattern in job_role_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        summary_info['직무'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 직무: {summary_info['직무']}")
                        break
                
                # 경력 패턴
                experience_patterns = [
                    r'경력\s*[:：]\s*([^<\n]+)',
                    r'경력</dt>\s*<dd[^>]*>([^<]+)',
                    r'경력\s*</th>\s*<td[^>]*>([^<]+)',
                    r'(\d+\s*[~-]\s*\d+년)'
                ]
                
                for pattern in experience_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        summary_info['경력'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 경력: {summary_info['경력']}")
                        break
                
                # 고용형태 패턴
                employment_type_patterns = [
                    r'고용형태\s*[:：]\s*([^<\n]+)',
                    r'고용형태</dt>\s*<dd[^>]*>([^<]+)',
                    r'고용형태\s*</th>\s*<td[^>]*>([^<]+)',
                    r'정규직|계약직|인턴|파견직|프리랜서'
                ]
                
                for pattern in employment_type_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        summary_info['고용형태'] = match.group(1).strip() if match.groups() else match.group(0).strip()
                        logger.info(f"정규식으로 찾은 고용형태: {summary_info['고용형태']}")
                        break
                
                # 근무지역 패턴
                location_patterns = [
                    r'근무지역\s*[:：]\s*([^<\n]+)',
                    r'근무지역</dt>\s*<dd[^>]*>([^<]+)',
                    r'근무지역\s*</th>\s*<td[^>]*>([^<]+)',
                    r'서울|경기|인천|부산|대구|대전|광주|울산|세종|강원|충북|충남|전북|전남|경북|경남|제주'
                ]
                
                for pattern in location_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        summary_info['근무지역'] = match.group(1).strip() if match.groups() else match.group(0).strip()
                        logger.info(f"정규식으로 찾은 근무지역: {summary_info['근무지역']}")
                        break
                
                # 스킬 패턴
                skills_patterns = [
                    r'스킬\s*[:：]\s*([^<\n]+)',
                    r'스킬</dt>\s*<dd[^>]*>([^<]+)',
                    r'스킬\s*</th>\s*<td[^>]*>([^<]+)'
                ]
                
                for pattern in skills_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        summary_info['스킬'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 스킬: {summary_info['스킬']}")
                        break
            except Exception as e:
                logger.warning(f"정규식 검색 중 오류 발생: {e}")
        
        # 이미지 구조 기반 추출 (사용자가 제공한 이미지 참고)
        try:
            # 요약 섹션 찾기
            summary_elements = driver.find_elements(By.CSS_SELECTOR, '.jp-jobs-detail-summary-item, .summary-item, .job-summary-item')
            for element in summary_elements:
                try:
                    label = element.find_element(By.CSS_SELECTOR, '.label, dt, th, .item-label').text.strip()
                    value = element.find_element(By.CSS_SELECTOR, '.value, dd, td, .item-value').text.strip()
                    
                    if '마감일' in label:
                        summary_info['마감일'] = value
                    elif '직무' in label:
                        summary_info['직무'] = value
                    elif '경력' in label:
                        summary_info['경력'] = value
                    elif '고용형태' in label:
                        summary_info['고용형태'] = value
                    elif '근무지역' in label:
                        summary_info['근무지역'] = value
                    elif '스킬' in label:
                        summary_info['스킬'] = value
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"이미지 구조 기반 추출 중 오류 발생: {e}")
        
        return summary_info
    
    def extract_job_description(self, driver):
        """주요 업무 추출"""
        job_description_selectors = [
            '.jp-jobs-detail-description .job-description',
            '.job-description',
            '.description-section',
            '.job-detail-description',
            '.job-posting-description',
            '.description-info',
            '.job-detail-section:contains("주요 업무")',
            '.job-responsibilities',
            '.main-responsibilities',
            '[data-test="job-description"]'
        ]
        
        job_description = self.extract_with_multiple_selectors(driver, job_description_selectors)
        
        # 페이지 소스에서 정규식으로 찾기
        if not job_description:
            try:
                page_source = driver.page_source
                
                job_description_patterns = [
                    r'주요\s*업무[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)',
                    r'담당\s*업무[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)',
                    r'업무\s*내용[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)'
                ]
                
                for pattern in job_description_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        # HTML 태그 제거
                        job_description = re.sub(r'<[^>]*>', ' ', match.group(1))
                        # 연속된 공백 제거
                        job_description = re.sub(r'\s+', ' ', job_description).strip()
                        logger.info(f"정규식으로 찾은 주요 업무: {job_description[:100]}...")
                        break
            except Exception as e:
                logger.warning(f"정규식 검색 중 오류 발생: {e}")
        
        return job_description
    
    def extract_requirements(self, driver):
        """자격 요건 추출"""
        requirements_selectors = [
            '.jp-jobs-detail-requirements .requirements',
            '.requirements',
            '.requirements-section',
            '.job-detail-requirements',
            '.job-posting-requirements',
            '.requirements-info',
            '.job-detail-section:contains("자격 요건")',
            '.job-qualifications',
            '.qualifications',
            '[data-test="requirements"]'
        ]
        
        requirements = self.extract_with_multiple_selectors(driver, requirements_selectors)
        
        # 페이지 소스에서 정규식으로 찾기
        if not requirements:
            try:
                page_source = driver.page_source
                
                requirements_patterns = [
                    r'자격\s*요건[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)',
                    r'지원\s*자격[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)',
                    r'자격\s*조건[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)'
                ]
                
                for pattern in requirements_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        # HTML 태그 제거
                        requirements = re.sub(r'<[^>]*>', ' ', match.group(1))
                        # 연속된 공백 제거
                        requirements = re.sub(r'\s+', ' ', requirements).strip()
                        logger.info(f"정규식으로 찾은 자격 요건: {requirements[:100]}...")
                        break
            except Exception as e:
                logger.warning(f"정규식 검색 중 오류 발생: {e}")
        
        return requirements
    
    def extract_company_location(self, driver):
        """회사 위치 추출"""
        location_selectors = [
            '.jp-jobs-detail-company-location .company-location',
            '.company-location',
            '.location-section',
            '.job-detail-company-location',
            '.job-posting-company-location',
            '.location-info',
            '.job-detail-section:contains("회사 위치")',
            '.company-address',
            '.address',
            '[data-test="company-location"]'
        ]
        
        company_location = self.extract_with_multiple_selectors(driver, location_selectors)
        
        # 페이지 소스에서 정규식으로 찾기
        if not company_location:
            try:
                page_source = driver.page_source
                
                location_patterns = [
                    r'회사\s*위치[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)',
                    r'근무\s*지역[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)',
                    r'주소[^<]*(?:<[^>]*>)*\s*([\s\S]*?)(?:<\/div>|<\/section>|<h2>|<h3>)',
                    r'서울시[^<]*(?:[가-힣]+구[^<]*(?:[가-힣]+로|[가-힣]+길)[^<]*\d+)'
                ]
                
                for pattern in location_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        # HTML 태그 제거
                        company_location = re.sub(r'<[^>]*>', ' ', match.group(1))
                        # 연속된 공백 제거
                        company_location = re.sub(r'\s+', ' ', company_location).strip()
                        logger.info(f"정규식으로 찾은 회사 위치: {company_location}")
                        break
            except Exception as e:
                logger.warning(f"정규식 검색 중 오류 발생: {e}")
        
        return company_location
    
    def crawl_job_posting(self, url):
        """채용 공고 크롤링"""
        logger.info(f"채용 공고 크롤링 시작: {url}")
        
        for retry in range(self.max_retries):
            try:
                driver = self.setup_driver()
                driver.get(url)
                
                # 페이지 로딩 대기
                logger.info(f"페이지 로딩 대기 중... ({self.wait_time}초)")
                time.sleep(self.wait_time)
                
                # 데이터 초기화
                job_data = {
                    'site': self.site_name,
                    'url': url,
                    'summary': {},
                    'job_description': '',
                    'requirements': '',
                    'company_location': ''
                }
                
                # 요약 정보 추출
                summary_info = self.extract_summary_info(driver)
                if summary_info:
                    job_data['summary'] = summary_info
                    logger.info(f"요약 정보 추출 성공: {summary_info}")
                
                # 주요 업무 추출
                job_description = self.extract_job_description(driver)
                if job_description:
                    job_data['job_description'] = job_description
                    logger.info(f"주요 업무 추출 성공: {job_description[:100]}...")
                
                # 자격 요건 추출
                requirements = self.extract_requirements(driver)
                if requirements:
                    job_data['requirements'] = requirements
                    logger.info(f"자격 요건 추출 성공: {requirements[:100]}...")
                
                # 회사 위치 추출
                company_location = self.extract_company_location(driver)
                if company_location:
                    job_data['company_location'] = company_location
                    logger.info(f"회사 위치 추출 성공: {company_location}")
                
                logger.info("채용 공고 크롤링 완료")
                driver.quit()
                
                self.data = job_data
                return job_data
            
            except Exception as e:
                logger.error(f"채용 공고 크롤링 중 오류 발생 (시도 {retry+1}/{self.max_retries}): {e}")
                if driver:
                    driver.quit()
                
                if retry < self.max_retries - 1:
                    logger.info(f"{5 * (retry + 1)}초 후 재시도합니다...")
                    time.sleep(5 * (retry + 1))
                else:
                    logger.error("최대 재시도 횟수를 초과했습니다.")
                    return None
    
    def save_to_json(self, filename):
        """수집한 데이터를 JSON 파일로 저장"""
        if not self.data:
            logger.warning("저장할 데이터가 없습니다.")
            return None
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"데이터가 성공적으로 저장되었습니다: {filename}")
        return filename
    
    def format_output(self):
        """결과를 포맷팅하여 출력"""
        if not self.data:
            return "크롤링된 데이터가 없습니다."
        
        output = []
        
        # 요약 정보
        output.append("요약")
        for key, value in self.data.get('summary', {}).items():
            output.append(f"{key}\n{value}")
        
        # 주요 업무
        if self.data.get('job_description'):
            output.append("\n주요 업무")
            output.append(self.data['job_description'])
        
        # 자격 요건
        if self.data.get('requirements'):
            output.append("\n자격 요건")
            output.append(self.data['requirements'])
        
        # 회사 위치
        if self.data.get('company_location'):
            output.append("\n회사위치")
            output.append(self.data['company_location'])
        
        return "\n".join(output)


def crawl_jobplanet(url):
    """잡플래닛 채용공고 크롤링 함수"""
    crawler = JobPlanetCrawler()
    job_data = crawler.crawl_job_posting(url)
    
    if job_data:
        # JSON 파일로 저장
        json_file = crawler.save_to_json("jobplanet_job.json")
        print(f"결과가 {json_file} 파일에 저장되었습니다.")
        
        # 포맷팅된 결과 출력
        formatted_output = crawler.format_output()
        print("\n" + "=" * 80)
        print("크롤링 결과")
        print("=" * 80)
        print(formatted_output)
        print("=" * 80)
        
        return job_data
    else:
        print("크롤링에 실패했습니다.")
        return None


if __name__ == "__main__":
    # 테스트 URL
    test_url = "https://www.jobplanet.co.kr/job/search?posting_ids%5B%5D=1290437"
    
    print("=" * 80)
    print("잡플래닛 채용공고 크롤러 테스트 시작")
    print("=" * 80)
    print(f"테스트 URL: {test_url}")
    
    # 크롤링 실행
    crawl_jobplanet(test_url)
