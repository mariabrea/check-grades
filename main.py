from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import db
import smtplib
import sys
import os
from email.message import EmailMessage
from dotenv import load_dotenv

print(sys.executable)

load_dotenv()

DPS109_SITE = "https://www.dps109.org"
CHANGES_FILE = "changes.csv"


class Dps109:

    def __init__(self):
        service = Service(os.getenv("EDGE_DRIVER_PATH"))
        self.driver = webdriver.Edge(service=service)
        self.driver.get(DPS109_SITE)
        self.grades = {}

    def search_family_access(self):
        time.sleep(2)
        button_family_access = self.driver.find_element(By.ID, 'icon-set-1-icon-number2')
        button_family_access.click()

    def login_family_access(self):
        time.sleep(3)
        input_user = self.driver.find_element(By.ID, 'UserName')
        input_user.send_keys(os.getenv("USER_FAMILY_ACCESS"))
        time.sleep(2)
        input_password = self.driver.find_element(By.ID, 'Password')
        input_password.send_keys(os.getenv("PASSWORD_FAMILY_ACCESS"))
        time.sleep(2)
        button_login = self.driver.find_element(By.XPATH, '/html/body/div/div[1]/div[2]/div/form/fieldset/button')
        button_login.click()

    def find_grades(self):
        changes_count = 0
        with open(CHANGES_FILE, "w") as file:
            time.sleep(2)
            button_grades = self.driver.find_element(By.ID, '9069-studentGrades_Widget')
            button_grades.click()
            time.sleep(4)
            rows_subjects = self.driver.find_element(By.CLASS_NAME, 'browseBody').find_elements(By.TAG_NAME, 'tr')

            for row_subject in (5, 10, 15, 25, 30, 35, 40, 45, 50, 55):
                time.sleep(2)
                columns_subject = rows_subjects[row_subject].find_elements(By.TAG_NAME, 'td')
                subject_name = columns_subject[0].find_element(By.CLASS_NAME, 'underlineText').text
                file.write(f"\n{subject_name}\n")
                try:
                    subject_grade_button = columns_subject[4].find_element(By.CLASS_NAME, 'linkPanelButton')
                    subject_grade = subject_grade_button.text
                    self.grades[subject_name] = subject_grade
                    print(f"{subject_name}-{subject_grade}")
                    # db.add_new_grade(subject_name, subject_grade)
                    subject = db.get_subject(subject_name)
                    # update the subject grade if it changed
                    # if subject_name == "SCIENCE":
                    #     subject_grade = "B+"
                    if subject.grade != subject_grade:
                        changes_count += 1
                        file.write(f"Grade changed from {subject.grade} to {subject_grade}\n")
                        db.update_subject_grade(subject, subject_grade)
                    else:
                        file.write(f"{subject_grade}\n")

                    time.sleep(2)
                    parent = self.driver.current_window_handle
                    subject_grade_button.click()
                    time.sleep(5)
                    tabs = self.driver.window_handles
                    self.driver.switch_to.window(tabs[1])
                    rows = self.driver.find_element(By.ID, 'SegmentedGradeBucketAssignments_body').find_elements(
                        By.TAG_NAME, 'tr')
                    for row in rows:
                        columns = row.find_elements(By.TAG_NAME, 'td')
                        assignment_description = columns[1].text
                        # if assignment_description == "Lab Safety PSA":
                        #     assignment_description = "Prueba5"
                        if assignment_description == "Exhibits Commitment and Perseverance":
                            break

                        assignment_letter = columns[3].text
                        assignment_score = columns[4].text
                        print(assignment_description)
                        print(assignment_letter)
                        print(assignment_score)
                        if db.assignment_exist(assignment_description=assignment_description):
                            assignment = db.get_assignment(assignment_description)
                            if assignment.grade != assignment_letter:
                                changes_count += 1
                                file.write(f"{assignment_description}->Grade changed from {assignment.grade} to {assignment_letter}\n")
                                db.update_assignment_grade(assignment, assignment_letter)
                        else:
                            changes_count += 1
                            db.add_new_assignment(subject_id=subject.id, description=assignment_description, grade=assignment_letter, score=assignment_score)
                            file.write(f"{assignment_description}-> Grade: {assignment_letter} -> Score: {assignment_score}\n")

                    self.driver.close()
                    self.driver.switch_to.window(parent)

                except NoSuchElementException:
                    subject_grade = ""
                    self.grades[subject_name] = subject_grade
                    print(f"{subject_name}-{subject_grade}")
                    # db.add_new_grade(subject_name, subject_grade)

            file.close()
            return changes_count

    def print_grades(self):
        print(self.grades)

    def close(self):
        self.driver.close()


def send_email():
    with open(file=CHANGES_FILE) as file:
        text = file.read()
        with smtplib.SMTP("smtp-mail.outlook.com", port=587) as connection:
            email = EmailMessage()
            email['from'] = os.getenv("MY_EMAIL")
            email['to'] = os.getenv("MY_EMAIL")
            email['subject'] = f"Yago's Grades Changed!"
            email.set_content(text)
            connection.starttls()
            connection.login(user=os.getenv("MY_EMAIL"), password=os.getenv("MY_PASSWORD"))
            connection.send_message(email)
    file.close()


dps109 = Dps109()
dps109.search_family_access()
dps109.login_family_access()
number_of_changes = dps109.find_grades()
if number_of_changes > 0:
    send_email()
dps109.close()
