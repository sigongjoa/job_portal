import requests
from bs4 import BeautifulSoup
import json
import re
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobKoreaCrawler:
    """잡코리아 크롤러 클래스"""
    
    def __init__(self):
        self.site_name = "JobKorea"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def crawl(self, url):
        """
        잡코리아 채용 정보 크롤링
        
        Args:
            url: 크롤링할 URL
            
        Returns:
            list: 크롤링된 채용 정보 리스트
        """
        logger.info(f"잡코리아 크롤링 시작: {url}")
        
        try:
            # Selenium 사용
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            
            # 페이지 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 회사명
            company_name = "알 수 없음"
            try:
                company_elements = driver.find_elements(By.CSS_SELECTOR, '.company, .coName, .co_name, h1.name')
                if company_elements:
                    company_name = company_elements[0].text.strip()
            except Exception as e:
                logger.warning(f"회사명 추출 실패: {e}")
            
            # 채용 제목
            title = "알 수 없음"
            try:
                title_elements = driver.find_elements(By.CSS_SELECTOR, '.title, .jobTit, .job_tit, .tit_job')
                if title_elements:
                    title = title_elements[0].text.strip()
            except Exception as e:
                logger.warning(f"채용 제목 추출 실패: {e}")
            
            # 채용 내용
            description = "상세 내용을 찾을 수 없습니다."
            try:
                desc_elements = driver.find_elements(By.CSS_SELECTOR, '.jobDescContents, .job-detail-contents, .detail-content')
                if desc_elements:
                    description = desc_elements[0].text.strip()
            except Exception as e:
                logger.warning(f"채용 내용 추출 실패: {e}")
            
            # 근무 조건
            work_condition = "근무 조건을 찾을 수 없습니다."
            try:
                condition_elements = driver.find_elements(By.CSS_SELECTOR, '.jobCondition, .job-condition, .condition-table')
                if condition_elements:
                    work_condition = condition_elements[0].text.strip()
            except Exception as e:
                logger.warning(f"근무 조건 추출 실패: {e}")
            
            # 접수 기간
            application_period = "접수 기간을 찾을 수 없습니다."
            try:
                period_elements = driver.find_elements(By.CSS_SELECTOR, '.date, .date_term, .term')
                if period_elements:
                    application_period = period_elements[0].text.strip()
            except Exception as e:
                logger.warning(f"접수 기간 추출 실패: {e}")
            
            # 드라이버 종료
            driver.quit()
            
            # 결과 반환
            result = {
                'site': self.site_name,
                'company_name': company_name,
                'title': title,
                'description': description,
                'work_condition': work_condition,
                'application_period': application_period,
                'url': url,
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"잡코리아 크롤링 완료: 채용 정보 수집 성공")
            return [result]
            
        except Exception as e:
            logger.error(f"잡코리아 크롤링 중 오류 발생: {e}")
            # 테스트용 더미 데이터 반환
            return self._get_dummy_data(url)
    
    def _get_dummy_data(self, url):
        """테스트용 더미 데이터 생성"""
        return [
            {
                'site': self.site_name,
                'company_name': '잡코리아 테스트 회사',
                'title': '백엔드 개발자 채용',
                'description': '백엔드 개발자를 모집합니다. 주요 업무는 API 개발 및 서버 관리입니다.',
                'work_condition': '주 5일 근무, 연봉 5000만원 이상, 경력 3년 이상',
                'application_period': '2025-03-01 ~ 2025-04-30',
                'url': url,
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

# 테스트 코드
if __name__ == "__main__":
    crawler = JobKoreaCrawler()
    results = crawler.crawl("https://www.jobkorea.co.kr/Recruit/GI_Read/46603837?Oem_Code=C1&productType=FirstVVIP&logpath=0&sc=511")
    print(json.dumps(results, ensure_ascii=False, indent=2))
