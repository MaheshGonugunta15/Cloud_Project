import datetime
import os
import re

import pymysql as pymysql
from flask import Flask, request, render_template, session, redirect


# conn = pymysql.connect(host="localhost", user="root", password="yourpassword", db="Freelancer")
# cursor = conn.cursor()


conn = pymysql.connect(host="database-1.czquikyoms9t.us-east-1.rds.amazonaws.com", user="admin", password="adminroot", db="Freelancer")
cursor = conn.cursor()

import boto3 as boto3
Freelancer_System_Access_Key = "AKIA5IJOXBK3ZWUXXM7S"
Freelancer_System_Secret_Access_Key = "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"
Freelancer_System_bucket = "freelancer-bucket-cc"
Freelancer_System_Email_Source = 'gm6714gm@gmail.com'
Freelancer_System_s3_client = boto3.client('s3', aws_access_key_id=Freelancer_System_Access_Key, aws_secret_access_key=Freelancer_System_Secret_Access_Key)
Freelancer_System_ses_client = boto3.client('ses', aws_access_key_id=Freelancer_System_Access_Key, aws_secret_access_key=Freelancer_System_Secret_Access_Key, region_name='us-east-1')



app = Flask(__name__)
app.secret_key = "freelancer"


App_Root = os.path.dirname(__file__)
App_Root = App_Root + "/static"


status_application_posted = "Client Posted Application"
status_applied_for_project = "Developer Applied for Project"
status_application_accepted = "Application Accepted by Client"
status_application_rejected = "Application rejected by Client"
status_add_schedule = "Schedule Added by Client"
status_schedule_accepted = "Schedule Accepted by Developer"
status_schedule_rejected = "Schedule Rejected by Developer"
status_first_payment = "10% amount Deposited to Developer"
status_Development_Started = "Project Development Started"
status_project_completed = "Project Completed"



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/adminLogin")
def adminLogin():
    return render_template("adminLogin.html")


@app.route("/adminLogin1", methods=['post'])
def adminLogin1():
    name = request.form.get("name")
    password = request.form.get("password")
    if name =='admin' and password =="admin":
        session['role'] = 'Admin'
        return redirect("/adminHome")
    else:
        return render_template("msg.html", message="Invalid Login Details", color="bg-danger text-white")


@app.route("/adminHome")
def adminHome():
    return render_template("adminHome.html")


@app.route("/clientLogin")
def clientLogin():
    return render_template("clientLogin.html")


@app.route("/clientLogin1", methods=['post'])
def clientLogin1():
    email = request.form.get('email')
    password = request.form.get('password')
    count = cursor.execute("select * from client where email='"+str(email)+"' and password='"+str(password)+"'")
    if count > 0:
        client = cursor.fetchone()
        if client[5] == "Verified":
            session['client_id'] = client[0]
            session['role'] = 'Client'
            name = client[1]
            email = client[2]
            emails = Freelancer_System_ses_client.list_identities(
                IdentityType='EmailAddress'
            )
            if email in emails['Identities']:
                email_msg = 'Hello ' + name + 'You Have Successfully Logged into Freelance Website'
                Freelancer_System_ses_client.send_email(Source=Freelancer_System_Email_Source,
                                                        Destination={'ToAddresses': [email]},
                                                        Message={
                                                            'Subject': {'Data': email_msg, 'Charset': 'utf-8'},
                                                            'Body': {'Html': {'Data': email_msg,
                                                                              'Charset': 'utf-8'}}})
            return redirect("/clientHome")
        else:
            return render_template("msg.html", message="Client is Not Activated", color="bg-danger text-white")
    else:
        return render_template("msg.html", message="Invalid Login Details", color="bg-danger text-white")


@app.route("/clientHome")
def clientHome():
    return render_template("clientHome.html")


@app.route("/clientRegistration")
def clientRegistration():
    return render_template("clientRegistration.html")


@app.route("/clientRegistration1", methods=['post'])
def clientRegistration1():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    password = request.form.get('password')
    address = request.form.get('address')
    about = request.form.get('about')
    status = "Not Verified"
    count = cursor.execute("select * from client where phone='"+str(phone)+"' or email='"+str(email)+"'")
    if count > 0:
        return render_template("msg.html", message="Duplicate Details", color="bg-danger text-white")
    cursor.execute("insert into client (name,phone,email,password,status,about,address) values('" + str(name) + "','" + str(
        phone) + "','" + str(email) + "','" + str(password) + "','" + str(status) + "','"+str(about)+"','"+str(address)+"')")
    conn.commit()
    Freelancer_System_ses_client.verify_email_address(
            EmailAddress=email
        )
    return redirect("/clientLogin")


@app.route("/viewClients")
def viewClients():
    cursor.execute("select * from client")
    clients = cursor.fetchall()
    return render_template("viewClients.html", clients=clients)


@app.route("/verifyClient")
def verifyClient():
    client_id = (request.args.get("client_id"))
    cursor.execute("update client set status='Verified' where client_id='"+str(client_id)+"'")
    conn.commit()
    cursor.execute("select * from client where client_id='"+str(client_id)+"'")
    client = cursor.fetchone()
    emails = Freelancer_System_ses_client.list_identities(
        IdentityType='EmailAddress'
    )
    if client[2] in emails['Identities']:
        email_msg = 'Hello ' + 'Your account is Activated'
        Freelancer_System_ses_client.send_email(Source=Freelancer_System_Email_Source,
                                                Destination={'ToAddresses': [client[2]]},
                                                Message={
                                                    'Subject': {'Data': email_msg, 'Charset': 'utf-8'},
                                                    'Body': {'Html': {'Data': email_msg,
                                                                      'Charset': 'utf-8'}}})
    return redirect("/viewClients")


@app.route("/notVerifyClient")
def notVerifyClient():
    client_id = (request.args.get("client_id"))
    cursor.execute("update client set status='Not Verified' where client_id='" + str(client_id) + "'")
    conn.commit()
    return redirect("/viewClients")


@app.route("/developerLogin")
def developerLogin():
    return render_template("developerLogin.html")


@app.route("/developerLogin1", methods=['post'])
def developerLogin1():
    email = request.form.get('email')
    password = request.form.get('password')
    count = cursor.execute("select * from developer where email='"+str(email)+"' and password='"+str(password)+"'")
    if count > 0:
        developer = cursor.fetchone()
        if developer[5] == "Verified":
            name = developer[1]
            email = developer[2]
            emails = Freelancer_System_ses_client.list_identities(
                IdentityType='EmailAddress'
            )
            if email in emails['Identities']:
                email_msg = 'Hello ' + name  + 'You Have Successfully Logged into Freelance System Website'
                Freelancer_System_ses_client.send_email(Source=Freelancer_System_Email_Source,
                                                             Destination={'ToAddresses': [email]},
                                                             Message={
                                                                 'Subject': {'Data': email_msg, 'Charset': 'utf-8'},
                                                                 'Body': {'Html': {'Data': email_msg,
                                                                                   'Charset': 'utf-8'}}})

            session['developer_id'] = developer[0]
            session['role'] = 'Developer'
            return redirect("/developerHome")
        else:
            return render_template("msg.html", message="Developer is Not Activated", color="bg-danger text-white")
    else:
        return render_template("msg.html", message="Invalid Login Details", color="bg-danger text-white")


@app.route("/developerHome")
def developerHome():
    cursor.execute("select * from developer where developer_id='"+str(session['developer_id'])+"'")
    developers = cursor.fetchall()
    return render_template("developerHome.html", developers=developers)


@app.route("/developerRegistration")
def developerRegistration():
    return render_template("developerRegistration.html")


@app.route("/developerRegistration1", methods=['post'])
def developerRegistration1():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    password = request.form.get('password')
    status = "Not Verified"
    count = cursor.execute("select * from developer where email='"+str(email)+"' or phone='"+str(phone)+"'")
    if count > 0:
        return render_template("msg.html", message="Duplicate Details", color="bg-danger text-white")
    cursor.execute("insert into developer (name,phone,email,password,status) values('"+str(name)+"','"+str(phone)+"','"+str(email)+"','"+str(password)+"','"+str(status)+"')")
    conn.commit()
    Freelancer_System_ses_client.verify_email_address(
        EmailAddress=email
    )
    return redirect("/developerLogin")


@app.route("/viewDevelopers")
def viewDevelopers():
    cursor.execute("select * from developer")
    developers = cursor.fetchall()
    # emailids = []
    # for developer in developers:
    #     email = developer[2]
    #     emailids.append(email)
    # print(emailids)
    # emails = Freelancer_System_ses_client.list_identities(
    #     IdentityType='EmailAddress'
    # )
    # sql = "select * from developer"
    # if emailids in emails['Identities']:
    #     for email in emailids:
    #         sql = "select * from developer where email = '" + str(email) + "'"
    # cursor.execute(sql)
    # developers = cursor.fetchall()
    return render_template("viewDevelopers.html", developers=developers)
    # return render_template("viewDevelopers.html", developers=developers)


@app.route("/verifyDeveloper")
def verifyDeveloper():
    developer_id = (request.args.get("developer_id"))
    cursor.execute("update developer set status='Verified' where developer_id='"+str(developer_id)+"'")
    conn.commit()
    cursor.execute("select * from developer where developer_id='"+str(developer_id)+"'")
    developer = cursor.fetchone()
    emails = Freelancer_System_ses_client.list_identities(
        IdentityType='EmailAddress'
    )
    if developer[2] in emails['Identities']:
        email_msg = 'Hello ' + 'Management your account is Activated'
        Freelancer_System_ses_client.send_email(Source=Freelancer_System_Email_Source,
                                                                 Destination={'ToAddresses': [developer[2]]},
                                                                 Message={
                                                                     'Subject': {'Data': email_msg, 'Charset': 'utf-8'},
                                                                     'Body': {'Html': {'Data': email_msg,
                                                                                       'Charset': 'utf-8'}}})
    return redirect("/viewDevelopers")


@app.route("/notVerifyDeveloper")
def notVerifyDeveloper():
    developer_id = (request.args.get("developer_id"))
    cursor.execute("update developer set status='Not Verified' where developer_id='" + str(developer_id) + "'")
    conn.commit()
    return redirect("/viewDevelopers")


@app.route("/uploadResume")
def uploadResume():
    return render_template("uploadResume.html")


@app.route("/uploadResume1", methods=['post'])
def uploadResume1():
    developer_id = session['developer_id']
    upload_resume = request.files.get("upload_resume")
    path = App_Root + "/resume/" + upload_resume.filename
    upload_resume.save(path)
    Freelancer_System_s3_client.upload_file(path, Freelancer_System_bucket, upload_resume.filename)
    cursor.execute("update developer set upload_resume='"+str(upload_resume.filename)+"' where developer_id='"+str(developer_id)+"'")
    conn.commit()
    return redirect("/developerHome")


@app.route("/categories")
def categories():
    cursor.execute("select * from category")
    categories = cursor.fetchall()
    return render_template("categories.html", categories=categories)


@app.route("/categories1", methods=['post'])
def categories1():
    category_name = request.form.get("category_name")
    cursor.execute("insert into category (category_name) values('"+str(category_name)+"')")
    conn.commit()
    return redirect("/categories")


@app.route("/view_projects")
def view_projects():
    category_id = request.args.get("category_id")
    skill = request.args.get("skill")
    project_title = request.args.get("project_title")


    if category_id == None :
        category_id = ''
    if skill == None:
        skill = ''
    if project_title == None:
        project_title = ''
    sql = ""
    if session['role']=='Client':
        client_id = session['client_id']
        if category_id == '' and skill == '' and project_title == '':
            sql = "select * from project where client_id='"+str(client_id)+"' and status!='Project Completed'"
        elif category_id == '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%"+str(project_title)+"%' and client_id='"+str(client_id)+"' and status!='Project Completed' "
            print(sql)
        elif category_id == '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%"+str(skill)+"%' and client_id='"+str(client_id)+"' and  status!='Project Completed'"
        elif category_id != '' and skill == '' and project_title == '':
            sql = "select * from project where category_id= '"+str(category_id)+"' and client_id='"+str(client_id)+"' and  status!='Project Completed'"
        elif category_id == '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%"+str(skill)+"%' or project_title like '%"+str(project_title)+"%' and client_id='"+str(client_id)+"' and  status!='Project Completed'"
        elif category_id != '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%" + str(project_title) + "%' and category_id ='"+str(category_id)+"' and client_id='"+str(client_id)+"'  and status!='Project Completed'"
        elif category_id != '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and category_id ='"+str(category_id)+"' and client_id='"+str(client_id)+"'  and status!='Project Completed'"
        elif category_id != '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and project_title like '%"+str(project_title)+"%'  and category_id ='" + str(
                category_id) + "' and client_id='"+str(client_id)+"' and  status!='Project Completed'"

    elif session['role']=='Developer':
        if category_id == '' and skill == '' and project_title == '':
            sql = "select * from project where  status!='Project Completed'"
        elif category_id == '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%"+str(project_title)+"%' and  status!='Project Completed'"
        elif category_id == '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%"+str(skill)+"%' and  status!='Project Completed'"
        elif category_id != '' and skill == '' and project_title == '':
            sql = "select * from project where category_id= '"+str(category_id)+"' and status!='Project Completed'"
        elif category_id == '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%"+str(skill)+"%' or project_title like '%"+str(project_title)+"%' and status!='Project Completed' "
        elif category_id != '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%" + str(project_title) + "%' and category_id ='"+str(category_id)+"' and status!='Project Completed'"
        elif category_id != '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and category_id ='"+str(category_id)+"' and status!='Project Completed'"
        elif category_id != '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and project_title like '%"+str(project_title)+"%'  and category_id ='" + str(
                category_id) + "' and status!='Project Completed'"

    elif session['role']=='Admin':
        if category_id == '' and skill == '' and project_title == '':
            sql = "select * from project where status!='Project Completed'"
        elif category_id == '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%"+str(project_title)+"%' and status!='Project Completed'"
        elif category_id == '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%"+str(skill)+"%' and status!='Project Completed'"
        elif category_id != '' and skill == '' and project_title == '':
            sql = "select * from project where category_id= '"+str(category_id)+"' and status!='Project Completed'"
        elif category_id == '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%"+str(skill)+"%' or project_title like '%"+str(project_title)+"%' and status!='Project Completed'"
        elif category_id != '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%" + str(project_title) + "%' and category_id ='"+str(category_id)+"' and status!='Project Completed'"
        elif category_id != '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and category_id ='"+str(category_id)+"' and status!='Project Completed'"
        elif category_id != '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and project_title like '%"+str(project_title)+"%'  and category_id ='" + str(
                category_id) + "' and status!='Project Completed'"
    cursor.execute(sql)
    project_details = cursor.fetchall()
    cursor.execute("select * from category")
    categories = cursor.fetchall()
    cursor.execute("select * from project")
    skills = cursor.fetchall()
    return render_template("view_projects.html",isReview=isReview,isAmountPaid=isAmountPaid,skills=skills, status_project_completed=status_project_completed, get_project_id_by_application=get_project_id_by_application, get_client_id_by_reviews=get_client_id_by_reviews, categories=categories, project_details=project_details, get_category_id=get_category_id, get_client_id=get_client_id, status_applied_for_project=status_applied_for_project, status_application_posted=status_application_posted, status_add_schedule=status_add_schedule, status_schedule_accepted=status_schedule_accepted, status_Development_Started=status_Development_Started)


@app.route("/history")
def history():
    category_id = request.args.get("category_id")
    skill = request.args.get("skill")
    project_title = request.args.get("project_title")

    if category_id == None:
        category_id = ''
    if skill == None:
        skill = ''
    if project_title == None:
        project_title = ''
    sql = ""
    if session['role'] == 'Client':
        client_id = session['client_id']
        if category_id == '' and skill == '' and project_title == '':
            sql = "select * from project where client_id='" + str(client_id) + "' and status='Project Completed'"
        elif category_id == '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%" + str(project_title) + "%' and client_id='" + str(
                client_id) + "' and status='Project Completed'"
            print(sql)
        elif category_id == '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and client_id='" + str(
                client_id) + "' and status='Project Completed'"
        elif category_id != '' and skill == '' and project_title == '':
            sql = "select * from project where category_id= '" + str(category_id) + "' and client_id='" + str(
                client_id) + "' and status='Project Completed' and status='Project Completed'"
        elif category_id == '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%" + str(skill) + "%' or project_title like '%" + str(
                project_title) + "%' and client_id='" + str(client_id) + "' and status='Project Completed'"
        elif category_id != '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%" + str(
                project_title) + "%' and category_id ='" + str(category_id) + "' and client_id='" + str(client_id) + "' and status='Project Completed'"
        elif category_id != '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and category_id ='" + str(
                category_id) + "' and client_id='" + str(client_id) + "' and status='Project Completed'"
        elif category_id != '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and project_title like '%" + str(
                project_title) + "%'  and category_id ='" + str(
                category_id) + "' and client_id='" + str(client_id) + "' and status='Project Completed'"

    elif session['role'] == 'Developer':
        if category_id == '' and skill == '' and project_title == '':
            sql = "select * from project where status='Project Completed'"
        elif category_id == '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%" + str(project_title) + "%' and status='Project Completed'"
        elif category_id == '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and status='Project Completed'"
        elif category_id != '' and skill == '' and project_title == '':
            sql = "select * from project where category_id= '" + str(category_id) + "' "
        elif category_id == '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%" + str(skill) + "%' or project_title like '%" + str(
                project_title) + "%' and status='Project Completed'"
        elif category_id != '' and skill == '' and project_title != '':
            sql = "select * from project where project_title like '%" + str(
                project_title) + "%' and category_id ='" + str(category_id) + "' and status='Project Completed'"
        elif category_id != '' and skill != '' and project_title == '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and category_id ='" + str(
                category_id) + "' and status='Project Completed'"
        elif category_id != '' and skill != '' and project_title != '':
            sql = "select * from project where skills like '%" + str(skill) + "%' and project_title like '%" + str(
                project_title) + "%'  and category_id ='" + str(
                category_id) + "' and status='Project Completed'"

    elif session['role'] == 'Admin':
        if category_id == '' and skill == '' and project_title == '':
            sql = "select * from project where status='Project Completed'"
    cursor.execute(sql)
    project_details = cursor.fetchall()
    cursor.execute("select * from category")
    categories = cursor.fetchall()
    cursor.execute("select * from project")
    skills = cursor.fetchall()
    return render_template("history.html",isAmountPaid=isAmountPaid,isReview=isReview,skills=skills, status_project_completed=status_project_completed, get_project_id_by_application=get_project_id_by_application, get_client_id_by_reviews=get_client_id_by_reviews, categories=categories, project_details=project_details, get_category_id=get_category_id, get_client_id=get_client_id, status_applied_for_project=status_applied_for_project, status_application_posted=status_application_posted, status_add_schedule=status_add_schedule, status_schedule_accepted=status_schedule_accepted, status_Development_Started=status_Development_Started)

def isAmountPaid(developer_id,project_id):
    count = cursor.execute("select * from payments where project_id='"+str(project_id)+"' and developer_id='"+str(developer_id)+"'")
    return count

def isReview(developer_id,project_id):
    count = cursor.execute("select * from reviews where project_id='"+str(project_id)+"' and developer_id='"+str(developer_id)+"'")

    return count

@app.route("/add_project")
def add_project():
    cursor.execute("select * from category")
    categories=  cursor.fetchall()
    return render_template("add_project.html", categories=categories)


@app.route("/add_project1", methods=['post'])
def add_project1():
    client_id = session['client_id']
    category_id = request.form.get("category_id")
    project_title = request.form.get("project_title")
    project_cost = request.form.get("project_cost")
    skills = request.form.get("skills")
    description = request.form.get("description")
    date = datetime.datetime.now()
    status = status_application_posted
    project_doc = request.files.get("project_doc")
    path = App_Root +"/document/" + project_doc.filename
    project_doc.save(path)
    picture_s3_file_name = project_doc.filename
    picture_image_url = f'https://{Freelancer_System_bucket}.s3.amazonaws.com/{picture_s3_file_name}'
    Freelancer_System_s3_client.upload_file(path, Freelancer_System_bucket, project_doc.filename)
    cursor.execute("insert into project (client_id,category_id,project_title,project_cost,skills,project_doc,description,date,status) "
                   "values('"+str(client_id)+"','"+str(category_id)+"','"+str(project_title)+"','"+str(project_cost)+"','"+str(skills)+"','"+str(picture_image_url)+"','"+str(description)+"','"+str(date)+"','"+str(status)+"')")
    conn.commit()
    return redirect("/view_projects")


def get_project_id_by_application(project_id):
    # query = {"project_id": ObjectId(project_id), "$or": [{"status": status_application_accepted}, {"status": status_project_completed}]}
    # application = application_col.find_one(query)
    cursor.execute("select * from developer where developer_id in (select developer_id from application where project_id='"+str(project_id)+"' and (status='"+str(status_application_accepted)+"' or status='"+str(status_project_completed)+"'))")
    developer = cursor.fetchone()
    return developer


def get_category_id(category_id):
    cursor.execute("select * from category where category_id='"+str(category_id)+"'")
    category = cursor.fetchone()
    return category


def get_client_id(client_id):
    cursor.execute("select * from client where client_id='"+str(client_id)+"'")
    client = cursor.fetchone()
    return client

def get_project_by_id(project_id):
    cursor.execute("select * from project where project_id='" + str(project_id) + "'")
    project = cursor.fetchone()
    return project


def get_developer_id(developer_id):
    cursor.execute("select * from developer where developer_id='"+str(developer_id)+"'")
    developer = cursor.fetchone()
    return developer


def get_project_id(project_id):
    cursor.execute("select * from project where project_id='"+str(project_id)+"'")
    project = cursor.fetchone()
    return project


@app.route("/apply_for_project")
def apply_for_project():
    project_id = request.args.get("project_id")
    return render_template("apply_for_project.html", project_id=project_id)


@app.route("/apply_for_project1", methods=['post'])
def apply_for_project1():
    developer_id = session['developer_id']
    project_id = request.form.get("project_id")
    upload_resume = request.files.get("upload_resume")
    path = App_Root + "/resume/" + upload_resume.filename
    upload_resume.save(path)
    date = datetime.datetime.now()
    status = status_applied_for_project
    # Freelancer_System_s3_client.upload_file(path, Freelancer_System_bucket, upload_resume.filename)
    picture_s3_file_name = upload_resume.filename
    # picture_image_url = f'https://{Freelancer_System_bucket}.s3.amazonaws.com/{picture_s3_file_name}'
    Freelancer_System_s3_client.upload_file(path, Freelancer_System_bucket, upload_resume.filename)
    cursor.execute("insert into application (developer_id,project_id,upload_resume,date,status)"
                   " values('"+str(developer_id)+"','"+str(project_id)+"','"+str(picture_s3_file_name)+"','"+str(date)+"','"+str(status)+"')")
    conn.commit()
    cursor.execute("update project set status='"+str(status_applied_for_project)+"' where project_id='"+str(project_id)+"'")
    conn.commit()

    return redirect("/view_projects")


@app.route("/view_applied_projects")
def view_applied_projects():
    project_id = request.args.get("project_id")
    cursor.execute("select * from application where project_id='"+str(project_id)+"'")
    applications = cursor.fetchall()
    return render_template("view_applied_projects.html", applications=applications, get_developer_id=get_developer_id, get_project_id=get_project_id, status_applied_for_project=status_applied_for_project, status_application_accepted=status_application_accepted, get_developer_id_by_reviews=get_developer_id_by_reviews)


@app.route("/accept_application")
def accept_application():
    project_id = request.args.get("project_id")
    application_id = request.args.get("application_id")
    cursor.execute("update application set status='"+str(status_application_accepted)+"' where application_id='"+str(application_id)+"'")
    conn.commit()
    cursor.execute("select * from application where application_id='"+str(application_id)+"' ")
    application = cursor.fetchone()
    cursor.execute("select * from developer where developer_id='"+str(application[5])+"'")
    developer = cursor.fetchone()
    print(developer)
    cursor.execute("select * from project where project_id='"+str(application[4])+"'")
    project = cursor.fetchone()

    emails = Freelancer_System_ses_client.list_identities(
        IdentityType='EmailAddress'
    )
    if developer[2] in emails['Identities']:
        email_msg = 'Hello ' + developer[
            1] + ' , Requested Project  ' + str(project[1]) + ' Application has been accepted by client'
        Freelancer_System_ses_client.send_email(Source=Freelancer_System_Email_Source,
                                                Destination={'ToAddresses': [developer[2]]},
                                                Message={
                                                    'Subject': {'Data': email_msg, 'Charset': 'utf-8'},
                                                    'Body': {'Html': {'Data': email_msg,
                                                                      'Charset': 'utf-8'}}})
    return redirect("/view_applied_projects?project_id="+str(project_id))


@app.route("/reject_application")
def reject_application():
    project_id = request.args.get("project_id")
    application_id = request.args.get("application_id")
    cursor.execute(
        "update application set status='" + str(status_application_rejected) + "' where application_id='" + str(
            application_id) + "'")
    conn.commit()
    cursor.execute("update project set status='"+str(status_application_posted)+"' where application_id='" + str(
            application_id) + "'")
    conn.commit()
    return redirect("/view_applied_projects?project_id="+str(project_id))


@app.route("/add_schedule")
def add_schedule():
    application_id = request.args.get("application_id")
    return render_template("add_schedule.html", application_id=application_id)


@app.route("/add_schedule1", methods=['post'])
def add_schedule1():
    application_id = request.form.get("application_id")
    cursor.execute("select * from application where application_id='"+str(application_id)+"'")
    application = cursor.fetchone()
    project_id = application[4]
    date_time = request.form.get("date_time")
    date_time = date_time.replace("T", " ")
    date_time = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M')
    schedule_status = status_add_schedule
    cursor.execute("insert into schedule(application_id,date_time,status,project_id) "
                   "values('"+str(application_id)+"','"+str(date_time)+"','"+str(schedule_status)+"','"+str(project_id)+"')")
    conn.commit()

    cursor.execute("update project set status='"+str(status_add_schedule)+"' where project_id='"+str(project_id)+"'")
    conn.commit()
    return redirect("/view_projects")


@app.route("/view_schedule")
def view_schedule():
    project_id = request.args.get("project_id")
    cursor.execute("select * from schedule where project_id='"+str(project_id)+"'")
    schedules = cursor.fetchall()
    return render_template("view_schedule.html",get_developer_id_by_reviews=get_developer_id_by_reviews, schedules=schedules, get_client_id=get_client_id, status_add_schedule=status_add_schedule, get_developer_id_by_application=get_developer_id_by_application, status_schedule_accepted=status_schedule_accepted,get_project_id=get_project_id)


def get_developer_id_by_reviews(developer_id):
    print("hiii")
    cursor.execute("select avg(rating) as rating from reviews where developer_id='"+str(developer_id)+"'")
    rating = cursor.fetchone()
    return rating[0]

def get_developer_id_by_application(application_id):
    cursor.execute("select * from developer where developer_id in (select developer_id from application where application_id='"+str(application_id)+"')")
    developer = cursor.fetchone()
    return developer


@app.route("/viewClientDetails")
def viewClientDetails():
    client_id = request.args.get("client_id")
    cursor.execute("select * from client where client_id='"+str(client_id)+"'")
    client = cursor.fetchone()
    return render_template("viewClientDetails.html", client=client)


@app.route("/viewProjectDetails")
def viewProjectDetails():
    project_id = request.args.get("project_id")
    # query = {"_id": ObjectId(project_id)}
    # project = project_col.find_one(query)
    return render_template("viewProjectDetails.html", get_category_id=get_category_id, get_client_id=get_client_id)


@app.route("/viewDeveloperDetails")
def viewDeveloperDetails():
    developer_id = request.args.get("developer_id")
    cursor.execute("select * from developer where developer_id='"+str(developer_id)+"'")
    developer = cursor.fetchone()
    return render_template("viewDeveloperDetails.html", developer=developer)


@app.route("/accept_schedule")
def accept_schedule():
    project_id = request.args.get("project_id")
    application_id = request.args.get("application_id")
    schedule_id = request.args.get("schedule_id")
    cursor.execute("update schedule set status='"+str(status_schedule_accepted)+"' where schedule_id='"+str(schedule_id)+"'")
    conn.commit()
    return redirect("/view_schedule?project_id="+str(project_id))


@app.route("/reject_schedule")
def reject_schedule():
    project_id = request.args.get("project_id")
    application_id = request.args.get("application_id")
    schedule_id = request.args.get("schedule_id")
    cursor.execute("update schedule set status='" + str(status_schedule_rejected) + "' where schedule_id='" + str(
        schedule_id) + "'")
    conn.commit()
    return redirect("/view_schedule?project_id="+str(project_id))


@app.route("/payAmount")
def payAmount():
    project_id = request.args.get("project_id")
    cursor.execute("select * from project where project_id='"+str(project_id)+"'")
    project = cursor.fetchone()
    price = project[2]
    amount = price
    developer_id = request.args.get("developer_id")
    return render_template("payAmount.html", project_id=project_id, developer_id=developer_id, amount=amount)


@app.route("/payAmount1", methods=['post'])
def payAmount1():
    project_id = request.form.get("project_id")
    developer_id = request.form.get("developer_id")
    amount = request.form.get("amount")
    date = datetime.datetime.now()
    cursor.execute("insert into  payments (project_id,developer_id,amount,date,status) "
                   "values ('"+str(project_id)+"','"+str(developer_id)+"','"+str(amount)+"','"+str(date)+"','Amount Paid')")
    conn.commit()
    return redirect("/view_projects")




@app.route("/view_payments")
def view_payments():
    project_id = request.args.get("project_id")
    query = ""
    if session['role'] == "Client":
        client_id = session['client_id']
        if project_id==None:
           query = "select * from payments where project_id in (select project_id from project where client_id='"+str(client_id)+"')"
        else:
            query = "select * from payments where project_id='" + str(project_id) + "'"
    elif session['role'] == "Admin":
        if project_id==None:
              query = "select * from payments"
        else:
            query = "select * from payments where project_id='" + str(project_id) + "'"

    elif session['role'] == "Developer":
        developer_id = session['developer_id']
        query = "select * from payments where developer_id='" + str(developer_id) + "'"
    cursor.execute(query)
    payments = cursor.fetchall()
    return render_template("view_payments.html",get_project_by_id=get_project_by_id, payments=payments,get_developer_id_by_application=get_developer_id_by_application, get_client_id=get_client_id)


# def get_developer_id_by_application_payments(application_id):
#     query = {"_id": ObjectId(application_id)}
#     application = application_col.find_one(query)
#     developer_id = application['developer_id']
#     query = {"_id": ObjectId(developer_id)}
#     developer = developer_col.find_one(query)
#     return developer


@app.route("/project_reviews")
def project_reviews():
    project_id = request.args.get("project_id")
    developer_id = request.args.get("developer_id")
    return render_template("project_reviews.html", project_id=project_id,developer_id=developer_id)


@app.route("/project_reviews1", methods=['get'])
def project_reviews1():
    project_id = request.args.get("project_id")
    developer_id = request.args.get("developer_id")
    rating = request.args.get('rating')
    review = request.args.get('review')
    date = datetime.datetime.now()
    cursor.execute("select * from project where project_id='"+str(project_id)+"'")
    project = cursor.fetchone()
    client_id = project[8]
    cursor.execute("insert into reviews (client_id,developer_id,rating,review,date,project_id) "
                   "values ('"+str(client_id)+"','"+str(developer_id)+"','"+str(rating)+"','"+str(review)+"','"+str(date)+"','"+str(project_id)+"')")
    conn.commit()
    return redirect("/project_reviews?project_id="+str(project_id))


# def get_developer_id_by_reviews(developer_id):
#     # query = {"developer_id": ObjectId(developer_id), "review_for": "Developer"}
#     #
#     # reviews = reviews_col.find(query)
#     # count = 0
#     # total_rating = 0
#     # for review in reviews:
#     #     total_rating = total_rating + int(review['rating'])
#     #     count = count + 1
#     # if count == 0:
#     #     return ""
#     # average_rating = total_rating/count
#     average_rating = 0
#     return average_rating


def get_client_id_by_reviews(client_id):
    # query = {"client_id": ObjectId(client_id), "review_for": "Client"}
    # reviews = reviews_col.find(query)
    # count = 0
    # total_rating = 0
    # for review in reviews:
    #     total_rating = total_rating + int(review['rating'])
    #     count = count + 1
    # if count == 0:
    #     return ""
    # average_rating = total_rating/count
    average_rating =0
    return average_rating


@app.route("/make_as_complete")
def make_as_complete():
    project_id = request.args.get("project_id")
    cursor.execute("update project set status='"+str(status_project_completed)+"' where project_id='"+str(project_id)+"'")
    conn.commit()
    cursor.execute("select * from application where status='"+str(status_application_accepted)+"' and project_id='"+str(project_id)+"'")
    application = cursor.fetchone()
    cursor.execute("update application set status='"+str(status_project_completed)+"' where application_id='"+str(application[0])+"'")
    conn.commit()
    cursor.execute("update schedule set status='"+str(status_project_completed)+"' where application_id='"+str(application[0])+"' and project_id='"+str(project_id)+"'")
    conn.commit()
    return redirect("/view_projects")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")


app.run(debug=True,port=80,host="0.0.0.0")
