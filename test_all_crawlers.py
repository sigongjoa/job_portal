import sys
import os
import json
from datetime import datetime

# 테스트 결과 저장 디렉토리
test_results_dir = '/home/ubuntu/crawler_test_results'
os.makedirs(test_results_dir, exist_ok=True)

# 크롤러 테스트 함수
def test_crawler(crawler_name, crawler_class, test_url, max_jobs=1):
    print(f"\n===== {crawler_name} 크롤러 테스트 시작 =====")
    
    try:
        # 크롤러 인스턴스 생성
        crawler = crawler_class()
        
        # 크롤링 실행
        start_time = datetime.now()
        results = crawler.crawl(test_url, max_jobs=max_jobs)
        end_time = datetime.now()
        
        # 소요 시간 계산
        duration = (end_time - start_time).total_seconds()
        
        # 결과 저장
        result_file = os.path.join(test_results_dir, f'{crawler_name.lower()}_test_result.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 결과 출력
        print(f"크롤링 완료: {len(results)}개 항목")
        print(f"소요 시간: {duration:.2f}초")
        print(f"결과 저장 경로: {result_file}")
        
        if results:
            print("\n첫 번째 결과 샘플:")
            print(json.dumps(results[0], ensure_ascii=False, indent=2))
        else:
            print("\n결과가 없습니다.")
        
        return {
            "success": True,
            "crawler": crawler_name,
            "items_count": len(results),
            "duration": duration,
            "result_file": result_file
        }
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        
        # 오류 결과 저장
        error_file = os.path.join(test_results_dir, f'{crawler_name.lower()}_error.json')
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump({"error": str(e)}, f, ensure_ascii=False, indent=2)
        
        return {
            "success": False,
            "crawler": crawler_name,
            "error": str(e),
            "error_file": error_file
        }
    finally:
        print(f"===== {crawler_name} 크롤러 테스트 완료 =====\n")

# 메인 테스트 함수
def run_all_tests():
    print("모든 크롤러 테스트 시작")
    
    test_results = []
    
    # 사람인 크롤러 테스트
    try:
        from final_saramin_crawler import FinalSaraminCrawler
        result = test_crawler(
            "Saramin", 
            FinalSaraminCrawler, 
            "https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=개발자"
        )
        test_results.append(result)
    except ImportError:
        print("사람인 크롤러 모듈을 찾을 수 없습니다.")
        test_results.append({
            "success": False,
            "crawler": "Saramin",
            "error": "모듈을 찾을 수 없습니다."
        })
    
    # 잡플래닛 크롤러 테스트
    try:
        from jobplanet_crawler import JobPlanetCrawler
        result = test_crawler(
            "JobPlanet", 
            JobPlanetCrawler, 
            "https://www.jobplanet.co.kr/job/search?q=개발자"
        )
        test_results.append(result)
    except ImportError:
        print("잡플래닛 크롤러 모듈을 찾을 수 없습니다.")
        test_results.append({
            "success": False,
            "crawler": "JobPlanet",
            "error": "모듈을 찾을 수 없습니다."
        })
    
    # 인크루트 크롤러 테스트
    try:
        from incruit_crawler import IncruitCrawler
        result = test_crawler(
            "Incruit", 
            IncruitCrawler, 
            "https://job.incruit.com/jobdb_info/popupjobpost.asp?job=2503250002286&inOut=In"
        )
        test_results.append(result)
    except ImportError:
        print("인크루트 크롤러 모듈을 찾을 수 없습니다.")
        test_results.append({
            "success": False,
            "crawler": "Incruit",
            "error": "모듈을 찾을 수 없습니다."
        })
    
    # 종합 결과 저장
    summary_file = os.path.join(test_results_dir, 'all_tests_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n모든 테스트 완료. 종합 결과: {summary_file}")
    return test_results

if __name__ == "__main__":
    run_all_tests()
