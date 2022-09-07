from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import time, os, shutil

class ExamBuilder(webdriver.Chrome):
    def __init__(self, email, password) -> None:
        self.email = email
        self.password = password
        super().__init__(service=Service(ChromeDriverManager().install()))

    def createDirs(self) -> None:
        if os.path.exists(self.courseName):
            shutil.rmtree(self.courseName)

        os.mkdir(self.courseName)

        for dir in [self.courseName, f"{self.courseName}/assets", f"{self.courseName}/assets/js",
                    f"{self.courseName}/assets/css", f"{self.courseName}/assets/images",
                    f"{self.courseName}/Exams",
                    f"{self.courseName}/Exams/{self.courseName}",
                    f"{self.courseName}/Exams/{self.courseName}/ExamBuilder",
                    f"{self.courseName}/Exams/{self.courseName}/ExamBuilder/Exam",
                    f"{self.courseName}/Exams/{self.courseName}/ExamBuilder/Flashcard"]:
            os.mkdir(f"{self.courseName}/{dir}")

    def getCourseName(self) -> str:
        return self.find_element(By.XPATH, '//*[@id="j_id0:j_id4:j_id35"]/header/div/div[1]/h3').text

    def setCourseName(self, courseName) -> None:
        self.courseName = f"{courseName} QBank"

    def openWebsite(self) -> None:
        self.get("https://apicommunity.force.com/api/API_Login")

    def login(self) -> None:
        self.find_element(By.NAME, "j_id0:theForm:j_id2:username").send_keys(self.email)
        self.find_element(By.NAME, "j_id0:theForm:j_id2:password").send_keys(self.password)
        self.find_element(By.ID, "j_id0:theForm:j_id2:LogInButton").click()

    def openAvailableCourse(self) -> None:
        self.find_element(By.XPATH, '//*[@id="j_id0:j_id4:j_id53:j_id65:0:j_id101"]').click()

    def clickOnExamTab(self) -> None:
        self.find_element(By.XPATH, '//*[@id="tabbed-navigation"]/ul/li[3]/a').click()
        self.setLink()

    def removeInProgress(self) -> bool:
        try:
            self.find_element(By.ID, "removeInProgress").click()
            time.sleep(2)
        except:
            return False

    def setLink(self) -> None:
        self.link = self.current_url

    def getExamTopics(self) -> None:
        topics = []
        mainSpan = self.find_element(By.XPATH, '//*[@id="j_id0:j_id4:j_id35:selectedTopicsPanel"]')
        for div in mainSpan.find_elements(By.XPATH, './div'):
            tableRows = div.find_elements(By.TAG_NAME, "tr")[1:]
            for row in tableRows:
                topicAndLength = row.find_element(By.XPATH, "./td[4]").text.split(" (")
                topics.append({
                    "name": topicAndLength[0],
                    "length": int(topicAndLength[1].replace(")", ""))
                })

            self.topics = topics


    def createExamTopicsIndexJson(self) -> None:
        dataArray = []

        examBuilderJson = {
            "course": self.courseName,
            "courseData": []
        }

        for mode in ["Exam", "Flashcard"]:
            examMode = {
                "examMode" : mode,
                "data": []
            }
            for topic in self.topics:
                topicJson = {
                    "name": topic["name"],
                    "length": topic["length"],
                    "assetp": f"Exams/{self.courseName}/ExamBuilder/{mode}/{topic['name']}.jsonp"
                }
                examMode["data"].append(topicJson)
            examBuilderJson["courseData"].append(
                examMode
            )

        dataArray.append(examBuilderJson)

        with open(f"{self.courseName}/{self.courseName}/Exams/assetExamBuilder.jsonp", "w") as file:
            file.write(f"data = {dataArray}")

    def scrapExamQuestions(self, length) -> list:
        questions = []

        for i in range(length):
            question = {
                "question": self.find_element(By.CLASS_NAME, "question-text").get_attribute("outerHTML"),
                "options": [],
                "correctAnswer": "",
                "exp": ""
            }

            for tr in self.find_element(By.CSS_SELECTOR, "table[role='presentation']").find_elements(By.TAG_NAME, 'tr'):
                question["options"].append(
                    f'<li>{tr.find_element(By.TAG_NAME, "label").text}/n</li>'
                )

            self.find_element(By.CSS_SELECTOR, "input[type='radio']").click()

            self.find_element(By.CSS_SELECTOR, 'input[value="Continue"]').click()

            explainationSpan = WebDriverWait(self,15).until( EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/span[2]/form/article/span[2]/span/section/div/div/span[1]")))

            question["correctAnswer"] = explainationSpan.find_element(By.XPATH, './p[2]').text[0]
            question["exp"] = explainationSpan.get_attribute("outerHTML")

            questions.append(question)

            if i < (length - 1):
                try:
                    self.find_element(By.CSS_SELECTOR, 'input[value="Next Question"]').click()
                    time.sleep(1.5)
                except:
                    print("WE HAVE AN EXCEPTION, WAITING FOR DEV")
                    time.sleep(400000)
        return questions

    def prepareExam(self, name, number) -> list:
        self.get(self.link)
        time.sleep(2)
        inputField = self.find_element(By.NAME, "j_id0:j_id4:j_id35:j_id242")
        inputField.send_keys(Keys.CONTROL, "a")
        inputField.send_keys(number)

        for tr in self.find_elements(By.TAG_NAME, "tr"):
            if name in tr.text:
                tr.find_element(By.CSS_SELECTOR, "input[type='checkbox']").click()
                time.sleep(3)
                self.find_element(By.CSS_SELECTOR, 'input[value="Create Exam"]').click()
                time.sleep(7)
                break

        return self.scrapExamQuestions(number)

    def createTopicQuestionsJsonp(self, name, array):
        with open(f"{self.courseName}/{self.courseName}/Exams/{self.courseName}/ExamBuilder/Exam/{name}.jsonp", 'w', encoding="utf-8") as file:
            file.write(f"data = {array}")
        with open(f"{self.courseName}/{self.courseName}/Exams/{self.courseName}/ExamBuilder/Flashcard/{name}.jsonp", 'w', encoding="utf-8") as file:
            file.write(f"data = {array}")

    def prepareAllExams(self) -> None:
        for topic in self.topics:
            name = topic["name"]
            length = topic["length"]

            allTopicQuestions = []

            while length != 0:
                if (length - 70) > 0:
                    length -= 70
                    questions = self.prepareExam(name, 70)
                    allTopicQuestions += questions
                    time.sleep(5)
                else:
                    questions = self.prepareExam(name, length)
                    allTopicQuestions += questions
                    length = 0
                    time.sleep(5)

            self.createTopicQuestionsJsonp(name, allTopicQuestions)

def main():
    email = input("Please input your email")
    password = input("Please input the password")

    with ExamBuilder(email, password) as exam:
        exam.openWebsite()
        time.sleep(2)
        exam.login()
        time.sleep(2)
        exam.openAvailableCourse()
        time.sleep(2)
        exam.clickOnExamTab()
        time.sleep(3)

        exam.setCourseName(exam.getCourseName())
        while exam.removeInProgress():
            pass

        exam.getExamTopics()
        exam.createDirs()

        exam.createExamTopicsIndexJson()
        exam.prepareAllExams()

main()