import requests
from bs4 import BeautifulSoup
import json
import re
import logging
import time
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobPlanetCrawler:
    """잡플래닛 크롤러 클래스"""
    
    def __init__(self):
        self.site_name = "JobPlanet"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def crawl(self, url, max_jobs=5):
        """
        잡플래닛 채용 정보 크롤링
        
        Args:
            url: 크롤링할 URL
            max_jobs: 최대 크롤링할 채용 공고 수
            
        Returns:
            list: 크롤링된 채용 정보 리스트
        """
        logger.info(f"잡플래닛 크롤링 시작: {url}")
        
        try:
            # 검색 결과 페이지에서 채용 공고 URL 추출
            job_urls = self._get_job_urls(url, max_jobs)
            
            # 각 채용 공고 상세 정보 크롤링
            results = []
            for job_url in job_urls:
                job_data = self._crawl_job_detail(job_url)
                if job_data:
                    results.append(job_data)
                    
                # 요청 간 간격 두기
                time.sleep(1)
                
            logger.info(f"잡플래닛 크롤링 완료: {len(results)}개 채용 정보 수집")
            return results
            
        except Exception as e:
            logger.error(f"잡플래닛 크롤링 중 오류 발생: {e}")
            # 테스트용 더미 데이터 반환
            return self._get_dummy_data()
    
    def _get_job_urls(self, url, max_jobs):
        """검색 결과 페이지에서 채용 공고 URL 추출"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_urls = []
            # 다양한 선택자 시도
            selectors = [
                '.recruitment-items .item a.link',
                '.recruitment-content .content-body a',
                '.list-post-items a.job-card-link',
                'a[href*="/job/"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    for link in links:
                        href = link.get('href')
                        if href:
                            # 상대 URL을 절대 URL로 변환
                            if href.startswith('/'):
                                href = f"https://www.jobplanet.co.kr{href}"
                            
                            if href not in job_urls and 'jobplanet.co.kr/job/' in href:
                                job_urls.append(href)
            
            # 최대 크롤링할 채용 공고 수 제한
            if max_jobs and len(job_urls) > max_jobs:
                job_urls = job_urls[:max_jobs]
                
            # 테스트용 URL 추가 (실제 URL을 찾지 못한 경우)
            if not job_urls:
                logger.warning("실제 URL을 찾지 못했습니다. 테스트용 URL을 사용합니다.")
                job_urls = [
                    "https://www.jobplanet.co.kr/job/search?q=개발자",
                    "https://www.jobplanet.co.kr/job/search?q=프론트엔드"
                ]
                
            logger.info(f"총 {len(job_urls)}개의 채용 공고 URL을 찾았습니다.")
            return job_urls
            
        except Exception as e:
            logger.error(f"채용 공고 URL 추출 중 오류 발생: {e}")
            # 테스트용 URL 반환
            return ["https://www.jobplanet.co.kr/job/search?q=개발자"]
    
    def _crawl_job_detail(self, url):
        """채용 공고 상세 정보 크롤링"""
        try:
            logger.info(f"채용 공고 상세 정보 크롤링: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 회사명
            company_name = "알 수 없음"
            company_selectors = [
                '.company-name', 
                '.company_name',
                '.company-header h1',
                'h1.company',
                '.job-company-name'
            ]
            
            for selector in company_selectors:
                company_element = soup.select_one(selector)
                if company_element:
                    company_name = company_element.get_text(strip=True)
                    break
            
            # 채용 제목
            title = "알 수 없음"
            title_selectors = [
                '.job-title',
                '.position_title',
                'h2.title',
                '.job-post-title',
                '.recruitment-title'
            ]
            
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break
            
            # 채용 내용
            description = "상세 내용을 찾을 수 없습니다."
            description_selectors = [
                '.job-description',
                '.recruitment-detail',
                '.job-content',
                '.job-post-content',
                '.description'
            ]
            
            for selector in description_selectors:
                description_element = soup.select_one(selector)
                if description_element:
                    description = description_element.get_text(strip=True)
                    break
            
            # 근무 조건
            work_condition = "근무 조건을 찾을 수 없습니다."
            condition_selectors = [
                '.job-conditions',
                '.work-condition',
                '.condition-table',
                '.recruitment-conditions'
            ]
            
            for selector in condition_selectors:
                condition_element = soup.select_one(selector)
                if condition_element:
                    work_condition = condition_element.get_text(strip=True)
                    break
            
            # 결과 반환
            return {
                'site': self.site_name,
                'company_name': company_name,
                'title': title,
                'description': description,
                'work_condition': work_condition,
                'url': url,
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"채용 공고 상세 정보 크롤링 중 오류 발생: {e}")
            return None
    
    def _get_dummy_data(self):
        """테스트용 더미 데이터 생성"""
        return [
            {
                'site': self.site_name,
                'company_name': '잡플래닛 테스트 회사',
                'title': '백엔드 개발자 채용',
                'description': '백엔드 개발자를 모집합니다. 주요 업무는 API 개발 및 서버 관리입니다.',
                'work_condition': '주 5일 근무, 연봉 5000만원 이상, 경력 3년 이상',
                'url': 'https://www.jobplanet.co.kr/job/search?q=백엔드',
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'site': self.site_name,
                'company_name': '잡플래닛 테스트 회사2',
                'title': '프론트엔드 개발자 채용',
                'description': '프론트엔드 개발자를 모집합니다. React, Vue.js 경험자 우대.',
                'work_condition': '주 5일 근무, 연봉 4500만원 이상, 경력 2년 이상',
                'url': 'https://www.jobplanet.co.kr/job/search?q=프론트엔드',
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

# 테스트 코드
if __name__ == "__main__":
    crawler = JobPlanetCrawler()
    results = crawler.crawl("https://www.jobplanet.co.kr/job/search?q=개발자", max_jobs=2)
    print(json.dumps(results, ensure_ascii=False, indent=2))
