import easyimap as e
import pandas as pd
import io, os, joblib, shutil
from pwacc import user, password
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from combination_counter.combination_counter import CombinationCounter

import os, sys

os.chdir('/'.join(sys.argv[0].split('/')[:-1]))

server=e.connect("imap.gmail.com",user,password)

files_read = joblib.load("files_read")

for idx in list(set(server.listids()) - set(files_read)):
    files_read.append(idx)
    joblib.dump(files_read, "files_read")
    email = server.mail(idx)
    if email.title == "convert":
        for attachment in email.attachments:
            file_name = attachment[0].split(".")
            if file_name[-1]=="xlsx":
                try:
                    df = pd.read_excel(io.BytesIO(email.attachments[0][1]))
                    if os.path.exists('processed_files'):
                        shutil.rmtree('processed_files')
                    os.makedirs('processed_files')
                    counter = CombinationCounter()
                    result = counter.count_combinations(df)
                    result[result['count']>3].sort_values('count',ascending=False).reset_index(drop=True).to_csv(f"processed_files/{file_name[0]}.csv")                
                    message = MIMEMultipart()
                    message["From"] = user
                    message['To'] = email.from_addr
                    message['Subject'] = f"Konvertierung von {file_name[0]}.xlsx erfolgreich :)"
                    attachment = open(f"processed_files/{file_name[0]}.csv",'rb')
                    obj = MIMEBase('application','octet-stream')
                    obj.set_payload((attachment).read())
                    encoders.encode_base64(obj)
                    obj.add_header('Content-Disposition',"attachment; filename= "+f"{file_name[0]}.csv")
                    message.attach(obj)
                    my_message = message.as_string()
                    email_session = smtplib.SMTP('smtp.gmail.com',587)
                    email_session.starttls()
                    email_session.login(user, password)
                    email_session.sendmail(user,email.from_addr,my_message)
                    email_session.quit()
                    print(f"Mail to {email.from_addr} has been sent")
                except:
                    print(f"Error in file {attachment[0]} from {email.from_addr}. File skipped.")