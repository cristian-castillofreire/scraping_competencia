import smtplib
from email.mime.text import MIMEText
myEmail = "performance.test.falabella.1@gmail.com"
myPassword = "guqzayrjftpiikpl"


smtp_server = "smtp.gmail.com"
smtp_port = 587

msg = MIMEText("This is a test email from Python script.")
msg['Subject'] = "Test Email"
msg['From'] = myEmail
msg['To'] = myEmail

server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()
server.login(myEmail, myPassword)

server.send_message(msg)
server.quit()