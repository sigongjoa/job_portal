import re
import logging
from urllib.parse import urlparse
from saramin_crawler import SaraminCrawler
from jobplanet_crawler import JobPlanetCrawler
from incruit_crawler import IncruitCrawler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_crawler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("IntegratedCrawler")

class IntegratedCrawler:
    """
    통합 크롤러 클래스
    URL을 분석하여 적절한 크롤러를 선택하고 실행
    """
    
    def __init__(self):
        self.crawlers = {
            'saramin': SaraminCrawler(),
            'jobplanet': JobPlanetCrawler(),
            'incruit': IncruitCrawler()
        }
    
    def detect_site(self, url):
        """
        URL을 분석하여 어떤 사이트인지 감지
        
        Args:
            url (str): 분석할 URL
            
        Returns:
            str: 감지된 사이트 이름 (saramin, jobplanet, incruit 중 하나)
                 감지 실패 시 None 반환
        """
        try:
            domain = urlparse(url).netloc.lower()
            
            if 'saramin.co.kr' in domain:
                return 'saramin'
            elif 'jobplanet.co.kr' in domain:
                return 'jobplanet'
            elif 'incruit.com' in domain:
                return 'incruit'
            else:
                logger.warning(f"지원하지 않는 사이트입니다: {domain}")
                return None
                
        except Exception as e:
            logger.error(f"사이트 감지 중 오류 발생: {e}")
            return None
    
    def crawl(self, url, max_jobs=None):
        """
        URL을 분석하여 적절한 크롤러를 선택하고 크롤링 실행
        
        Args:
            url (str): 크롤링할 URL
            max_jobs (int): 최대 크롤링할 채용 공고 수 (기본값: None, 모든 공고 크롤링)
            
        Returns:
            tuple: (사이트 이름, 크롤링 결과)
        """
        site = self.detect_site(url)
        
        if not site:
            logger.error(f"지원하지 않는 사이트입니다: {url}")
            return None, []
        
        logger.info(f"감지된 사이트: {site}, URL: {url}")
        
        try:
            crawler = self.crawlers[site]
            result = crawler.crawl(url, max_jobs)
            
            if result:
                logger.info(f"크롤링 성공: {site}, 총 {len(result)}개의 채용 공고를 수집했습니다.")
                # CSV 파일로 저장
                csv_file = crawler.save_to_csv()
                logger.info(f"데이터가 저장된 파일: {csv_file}")
            else:
                logger.warning(f"크롤링 결과가 없습니다: {site}, URL: {url}")
            
            return site, result
            
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {site}, URL: {url}, 오류: {e}")
            return site, []
    
    def crawl_multiple(self, urls, max_jobs_per_url=None):
        """
        여러 URL을 크롤링
        
        Args:
            urls (list): 크롤링할 URL 목록
            max_jobs_per_url (int): URL당 최대 크롤링할 채용 공고 수 (기본값: None, 모든 공고 크롤링)
            
        Returns:
            dict: {사이트 이름: 크롤링 결과} 형태의 딕셔너리
        """
        results = {}
        
        for url in urls:
            site, result = self.crawl(url, max_jobs_per_url)
            
            if site:
                if site not in results:
                    results[site] = []
                results[site].extend(result)
        
        return results


def main():
    """
    메인 함수
    """
    # 통합 크롤러 생성
    crawler = IntegratedCrawler()
    
    # 테스트할 URL 목록
    test_urls = [
        "https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=개발자",
        "https://www.jobplanet.co.kr/job/search?q=개발자",
        "https://www.incruit.com/list/search.asp?col=all&kw=개발자"
    ]
    
    # 각 URL 크롤링 테스트
    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"URL 테스트: {url}")
        print(f"{'='*50}")
        
        site, result = crawler.crawl(url, max_jobs=3)  # 테스트를 위해 각 사이트당 최대 3개의 공고만 크롤링
        
        if result:
            print(f"크롤링 성공: {site}, 총 {len(result)}개의 채용 공고를 수집했습니다.")
            
            # 결과 출력 (첫 번째 항목만)
            if len(result) > 0:
                print("\n첫 번째 채용 공고 정보:")
                for key, value in result[0].items():
                    if key == 'description':
                        print(f"{key}: {value[:100]}...")  # 설명은 처음 100자만 출력
                    else:
                        print(f"{key}: {value}")
        else:
            print(f"크롤링 실패: {site}, URL: {url}")
    
    print("\n모든 테스트가 완료되었습니다.")


if __name__ == "__main__":
    main()
