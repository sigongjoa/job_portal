import time
import json
import os
import re
from urllib.parse import urljoin
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """
    Selenium WebDriver를 설정합니다.
    
    Returns:
        WebDriver: 설정된 Chrome WebDriver
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 헤드리스 모드
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def crawl_incruit_job_with_selenium(url):
    """
    Selenium을 사용하여 인크루트 채용공고 페이지를 크롤링합니다.
    
    Args:
        url (str): 크롤링할 인크루트 채용공고 URL
        
    Returns:
        dict: 추출된 채용공고 정보
    """
    # 결과를 저장할 딕셔너리
    job_data = {
        "company_info": {},
        "job_details": {
            "text_content": [],
            "image_urls": []
        },
        "work_environment": {},
        "application_period": {},
        "salary_info": {},
        "benefits": []
    }
    
    driver = None
    
    try:
        # WebDriver 설정
        driver = setup_driver()
        
        # 페이지 로드
        print(f"페이지 로드 중: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 페이지 완전 로딩을 위한 추가 대기
        time.sleep(3)
        
        # 회사 기본정보 추출
        try:
            company_name_elem = driver.find_element(By.CSS_SELECTOR, 'a[href*="company_info"]')
            job_data["company_info"]["company_name"] = company_name_elem.text.strip()
        except NoSuchElementException:
            try:
                company_name_elem = driver.find_element(By.TAG_NAME, 'h2')
                job_data["company_info"]["company_name"] = company_name_elem.text.strip()
            except NoSuchElementException:
                job_data["company_info"]["company_name"] = "회사명을 찾을 수 없습니다."
        
        # 채용 제목 추출
        try:
            job_title = driver.find_element(By.CSS_SELECTOR, 'strong')
            job_data["company_info"]["job_title"] = job_title.text.strip()
        except NoSuchElementException:
            job_data["company_info"]["job_title"] = "채용 제목을 찾을 수 없습니다."
        
        # 기본 정보 테이블에서 정보 추출
        try:
            info_rows = driver.find_elements(By.CSS_SELECTOR, 'table tr')
            for row in info_rows:
                try:
                    th = row.find_element(By.TAG_NAME, 'th')
                    td = row.find_element(By.TAG_NAME, 'td')
                    key = th.text.strip()
                    value = td.text.strip()
                    
                    # 키에 따라 적절한 카테고리에 정보 저장
                    if '고용형태' in key:
                        job_data["company_info"]["employment_type"] = value
                    elif '근무지역' in key:
                        job_data["company_info"]["location"] = value
                    elif '급여조건' in key:
                        job_data["company_info"]["salary"] = value
                    elif '경력' in key:
                        job_data["company_info"]["experience"] = value
                    elif '학력' in key:
                        job_data["company_info"]["education"] = value
                    elif '우대사항' in key:
                        job_data["company_info"]["preferences"] = value
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            pass
        
        # 상세내용 탭 클릭
        try:
            detail_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '상세내용')]"))
            )
            detail_tab.click()
            time.sleep(2)  # 탭 전환 대기
        except (TimeoutException, NoSuchElementException):
            print("상세내용 탭을 찾을 수 없습니다.")
        
        # 상세 내용 추출 (텍스트 및 이미지)
        try:
            detail_section = driver.find_element(By.CSS_SELECTOR, 'div.cont_box')
            
            # 텍스트 내용 추출
            paragraphs = detail_section.find_elements(By.XPATH, './/p | .//div | .//span')
            for paragraph in paragraphs:
                text = paragraph.text.strip()
                if text and not text.isspace():
                    job_data["job_details"]["text_content"].append(text)
            
            # 이미지 URL 추출
            images = detail_section.find_elements(By.TAG_NAME, 'img')
            for img in images:
                img_url = img.get_attribute('src')
                if img_url:
                    job_data["job_details"]["image_urls"].append(img_url)
        except NoSuchElementException:
            print("상세 내용 섹션을 찾을 수 없습니다.")
        
        # 근무환경 정보 추출
        try:
            work_env_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '근무 유형') or contains(text(), '근무유형')]")
            if work_env_elements:
                work_env_element = work_env_elements[0]
                parent_element = work_env_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'cont_box')]")
                job_data["work_environment"]["description"] = parent_element.text.strip()
                
                # 근무 유형 정보 추출
                work_types = ["상시직", "단기상시직", "주말직"]
                for work_type in work_types:
                    if work_type in parent_element.text:
                        job_data["work_environment"][work_type] = True
                
                # 근무 시간 추출
                time_pattern = re.compile(r'일\s+(\d+)시간')
                time_match = time_pattern.search(parent_element.text)
                if time_match:
                    job_data["work_environment"]["근무시간"] = time_match.group(1) + "시간"
                
                # 근무 조건 추출
                work_conditions = ["주 5일 근무", "연장/특근 가능", "2개월~6개월 근무"]
                for condition in work_conditions:
                    if condition in parent_element.text:
                        job_data["work_environment"][condition] = True
        except (NoSuchElementException, IndexError):
            print("근무환경 정보를 찾을 수 없습니다.")
        
        # 직무 및 시급 정보 추출
        try:
            salary_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '직무') and contains(text(), '기본시급')]")
            if salary_elements:
                salary_element = salary_elements[0]
                parent_element = salary_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'cont_box')]")
                
                # 직무별 시급 정보 추출
                job_roles = ["조리보조", "홀서비스", "패스트푸드", "스낵", "렌탈", "라이프가드", "시재실", 
                             "어트랙션", "그린/주차", "티켓/그리팅", "상품판매"]
                
                for role in job_roles:
                    role_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{role}')]")
                    if role_elements:
                        role_element = role_elements[0]
                        parent_row = role_element.find_element(By.XPATH, "./ancestor::tr")
                        wage_elements = parent_row.find_elements(By.XPATH, ".//*[contains(text(), '원')]")
                        if wage_elements:
                            job_data["salary_info"][role] = wage_elements[0].text.strip()
        except (NoSuchElementException, IndexError):
            print("직무 및 시급 정보를 찾을 수 없습니다.")
        
        # 근무 혜택 정보 추출
        try:
            benefits_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '근무 혜택') or contains(text(), '근무혜택')]")
            if benefits_elements:
                benefits_element = benefits_elements[0]
                parent_element = benefits_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'cont_box')]")
                
                # 혜택 목록 추출
                benefits = [
                    "에버랜드 자유 이용", "기숙사 제공", "에버랜드 이용권 선물", "사원식당 식사 제공",
                    "파크 상품 할인", "수도권 셔틀 운영", "서비스 전문 교육 제공", "캐스트 수료 선물",
                    "평가 우수자 인센티브", "우수 캐스트 시상", "캐스트만의 축제/행사 진행", 
                    "근무 의상 지급", "4대 보험 가입", "웰니스 헬스장 운영"
                ]
                
                for benefit in benefits:
                    if benefit in parent_element.text:
                        job_data["benefits"].append(benefit)
        except (NoSuchElementException, IndexError):
            print("근무 혜택 정보를 찾을 수 없습니다.")
        
        # 접수기간 및 방법 추출
        try:
            application_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '접수기간') or contains(text(), '지원방법')]")
            if application_elements:
                application_element = application_elements[0]
                parent_element = application_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'cont_box')]")
                job_data["application_period"]["description"] = parent_element.text.strip()
                
                # 접수기간 추출
                period_pattern = re.compile(r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일|\d{1,2}월\s*\d{1,2}일|상시)')
                period_match = period_pattern.search(parent_element.text)
                if period_match:
                    job_data["application_period"]["접수기간"] = period_match.group(1)
                
                # 지원방법 추출
                if "지원방법" in parent_element.text:
                    method_pattern = re.compile(r'지원방법[^\n]*\n([^\n]+)')
                    method_match = method_pattern.search(parent_element.text)
                    if method_match:
                        job_data["application_period"]["지원방법"] = method_match.group(1).strip()
        except (NoSuchElementException, IndexError):
            print("접수기간 및 방법 정보를 찾을 수 없습니다.")
        
        # 데이터 정제
        # 빈 리스트나 딕셔너리 제거
        if not job_data["job_details"]["text_content"]:
            del job_data["job_details"]["text_content"]
        
        if not job_data["job_details"]["image_urls"]:
            del job_data["job_details"]["image_urls"]
        
        if not job_data["work_environment"]:
            job_data["work_environment"] = {"description": "정보를 찾을 수 없습니다."}
        
        if not job_data["application_period"]:
            job_data["application_period"] = {"description": "정보를 찾을 수 없습니다."}
        
        if not job_data["salary_info"]:
            job_data["salary_info"] = {"description": "정보를 찾을 수 없습니다."}
        
        if not job_data["benefits"]:
            job_data["benefits"] = ["정보를 찾을 수 없습니다."]
        
        return job_data
    
    except Exception as e:
        print(f"크롤링 중 오류 발생: {str(e)}")
        return {"error": str(e)}
    
    finally:
        if driver:
            driver.quit()

def save_to_json(data, filename):
    """
    데이터를 JSON 파일로 저장합니다.
    
    Args:
        data (dict): 저장할 데이터
        filename (str): 저장할 파일 이름
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"데이터가 {filename}에 저장되었습니다.")

def save_images(image_urls, save_dir):
    """
    이미지 URL에서 이미지를 다운로드하여 저장합니다.
    
    Args:
        image_urls (list): 이미지 URL 목록
        save_dir (str): 이미지를 저장할 디렉토리
    
    Returns:
        list: 저장된 이미지 파일 경로 목록
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    saved_images = []
    
    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 파일 확장자 추출
            content_type = response.headers.get('content-type', '')
            ext = '.jpg'  # 기본 확장자
            if 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            
            # 파일 저장
            filename = f"image_{i+1}{ext}"
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            saved_images.append(filepath)
            print(f"이미지가 {filepath}에 저장되었습니다.")
            
        except Exception as e:
            print(f"이미지 다운로드 중 오류 발생: {str(e)}")
    
    return saved_images

def validate_data(data):
    """
    크롤링된 데이터를 검증합니다.
    
    Args:
        data (dict): 검증할 데이터
        
    Returns:
        dict: 검증 결과
    """
    issues = []
    
    # 회사 기본정보 검증
    if not data.get("company_info"):
        issues.append("회사 기본정보가 없습니다.")
    else:
        if not data["company_info"].get("company_name") or data["company_info"]["company_name"] == "회사명을 찾을 수 없습니다.":
            issues.append("회사명이 없습니다.")
        if not data["company_info"].get("job_title") or data["company_info"]["job_title"] == "채용 제목을 찾을 수 없습니다.":
            issues.append("채용 제목이 없습니다.")
    
    # 상세 내용 검증
    if not data.get("job_details") or (not data["job_details"].get("text_content") and not data["job_details"].get("image_urls")):
        issues.append("상세 내용이 없습니다.")
    
    # 근무환경 검증
    if not data.get("work_environment") or data["work_environment"].get("description") == "정보를 찾을 수 없습니다.":
        issues.append("근무환경 정보가 없습니다.")
    
    # 접수기간 및 방법 검증
    if not data.get("application_period") or data["application_period"].get("description") == "정보를 찾을 수 없습니다.":
        issues.append("접수기간 및 방법 정보가 없습니다.")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues
    }

def main():
    # 테스트용 URL
    url = "https://job.incruit.com/jobdb_info/popupjobpost.asp?job=2503250002286&inOut=In"
    
    # 크롤링 실행
    print("인크루트 채용공고 크롤링을 시작합니다...")
    job_data = crawl_incruit_job_with_selenium(url)
    
    # 이미지 저장
    if "job_details" in job_data and "image_urls" in job_data["job_details"]:
        image_urls = job_data["job_details"]["image_urls"]
        if image_urls:
            print("채용공고 이미지를 다운로드합니다...")
            saved_images = save_images(image_urls, "incruit_images")
            job_data["job_details"]["saved_images"] = saved_images
    
    # 결과 저장
    save_to_json(job_data, "incruit_job_data_selenium.json")
    
    # 결과 출력
    print("\n크롤링 결과:")
    print(json.dumps(job_data, ensure_ascii=False, indent=2))
    
    # 데이터 검증
    print("\n데이터 검증:")
    validation_result = validate_data(job_data)
    if validation_result["is_valid"]:
        print("데이터가 성공적으로 크롤링되었습니다.")
    else:
        print("일부 데이터가 제대로 크롤링되지 않았습니다:")
        for issue in validation_result["issues"]:
            print(f"- {issue}")

if __name__ == "__main__":
    main()
