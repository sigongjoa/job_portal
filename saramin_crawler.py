from base_crawler import BaseCrawler
import re
import logging
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

class SaraminCrawler(BaseCrawler):
    """
    사람인(Saramin) 채용 사이트 크롤러
    """
    
    def __init__(self):
        super().__init__("Saramin")
    
    def crawl_job_list(self, url):
        """
        사람인 채용 공고 목록 페이지를 크롤링
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            list: 채용 공고 URL 목록
        """
        job_urls = []
        
        try:
            # Selenium으로 동적 페이지 로딩
            driver, soup = self.get_page_with_selenium(url)
            
            if not soup:
                self.logger.error("페이지 로딩 실패")
                if driver:
                    driver.quit()
                return []
            
            # 채용 공고 링크 추출
            job_items = soup.select('.item_recruit')
            
            for item in job_items:
                try:
                    # 채용 공고 링크 추출
                    link_tag = item.select_one('.area_job > h2 > a')
                    if link_tag and 'href' in link_tag.attrs:
                        job_url = link_tag['href']
                        # 상대 경로인 경우 절대 경로로 변환
                        if not job_url.startswith('http'):
                            job_url = urljoin('https://www.saramin.co.kr', job_url)
                        job_urls.append(job_url)
                except Exception as e:
                    self.logger.error(f"채용 공고 URL 추출 중 오류 발생: {e}")
            
            self.logger.info(f"총 {len(job_urls)}개의 채용 공고 URL을 찾았습니다.")
            
            if driver:
                driver.quit()
                
            return job_urls
            
        except Exception as e:
            self.logger.error(f"채용 공고 목록 크롤링 중 오류 발생: {e}")
            if 'driver' in locals() and driver:
                driver.quit()
            return []
    
    def crawl_job_detail(self, url):
        """
        사람인 채용 공고 상세 페이지를 크롤링
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            dict: 채용 공고 상세 정보
        """
        try:
            # Selenium으로 동적 페이지 로딩
            driver, soup = self.get_page_with_selenium(url)
            
            if not soup:
                self.logger.error(f"상세 페이지 로딩 실패: {url}")
                if driver:
                    driver.quit()
                return None
            
            # 기업명 추출
            company_name = ""
            company_tag = soup.select_one('.company_name')
            if company_tag:
                company_name = company_tag.text.strip()
            
            # 공고 제목 추출
            title = ""
            title_tag = soup.select_one('.tit_job')
            if title_tag:
                title = title_tag.text.strip()
            
            # 마감일 추출
            deadline = ""
            deadline_tag = soup.select_one('.info_period > .txt')
            if deadline_tag:
                deadline = deadline_tag.text.strip()
            
            # 근무지역 추출
            location = ""
            location_tag = soup.select_one('.info_work > .txt')
            if location_tag:
                location = location_tag.text.strip()
            
            # 경력 요구사항 추출
            experience = ""
            experience_tag = soup.select_one('.info_exp > .txt')
            if experience_tag:
                experience = experience_tag.text.strip()
            
            # 학력 요구사항 추출
            education = ""
            education_tag = soup.select_one('.info_edu > .txt')
            if education_tag:
                education = education_tag.text.strip()
            
            # 급여 정보 추출
            salary = ""
            salary_tag = soup.select_one('.info_salary > .txt')
            if salary_tag:
                salary = salary_tag.text.strip()
            
            # 고용형태 추출
            employment_type = ""
            employment_type_tag = soup.select_one('.info_employment > .txt')
            if employment_type_tag:
                employment_type = employment_type_tag.text.strip()
            
            # 상세 내용 추출
            description = ""
            description_tag = soup.select_one('#job_content')
            if description_tag:
                description = description_tag.text.strip()
            
            # 수집된 데이터 정리
            job_data = {
                'site': self.site_name,
                'url': url,
                'company_name': company_name,
                'title': title,
                'deadline': deadline,
                'location': location,
                'experience': experience,
                'education': education,
                'salary': salary,
                'employment_type': employment_type,
                'description': description
            }
            
            if driver:
                driver.quit()
                
            return job_data
            
        except Exception as e:
            self.logger.error(f"채용 공고 상세 크롤링 중 오류 발생: {url}, 오류: {e}")
            if 'driver' in locals() and driver:
                driver.quit()
            return None
